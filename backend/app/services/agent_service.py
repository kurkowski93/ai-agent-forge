import os
import json
import uuid
import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator, Callable, Union
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agents_forge.core_agent.agent import generate_core_agent
from agents_forge.agents_generation.generator import generate_agent_from_config
from agents_forge.agents_generation.config_schema import AgentConfig
from agents_forge.core_agent.utils.nodes import MAX_MESSAGES

# Configure logger
logger = logging.getLogger(__name__)

def _make_json_serializable(obj: Any) -> Any:
    """
    Converts objects to JSON-serializable formats.
    Recursively processes complex data structures.
    """
    # Handle Pydantic models
    if hasattr(obj, "model_dump"):  # Pydantic v2
        return obj.model_dump()
    elif hasattr(obj, "dict"):      # Pydantic v1
        return obj.dict()
    # Handle LangChain Message objects
    elif isinstance(obj, (HumanMessage, AIMessage, SystemMessage)):
        return {
            "type": obj.__class__.__name__,
            "content": obj.content,
            "additional_kwargs": obj.additional_kwargs
        }
    # Handle Enum objects
    elif hasattr(obj, "_value_") and hasattr(obj, "_name_"):
        return obj._value_
    # Recursively handle dictionaries
    elif isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    # Recursively handle lists
    elif isinstance(obj, list):
        return [_make_json_serializable(item) for item in obj]
    # Handle primitive types
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    # Handle other objects with __dict__
    elif hasattr(obj, "__dict__"):
        try:
            return _make_json_serializable(obj.__dict__)
        except:
            return str(obj)
    # Default fallback
    else:
        return str(obj)


async def format_sse_event(event_type: str, data: Any) -> str:
    """
    Format data as a Server-Sent Event (SSE).
    Handles data normalization and serialization.
    """
    serializable_data = _make_json_serializable(data)
    json_data = json.dumps(serializable_data)
    logger.debug(f"Sending SSE event: {event_type} with data length: {len(json_data)}")
    return f"event: {event_type}\ndata: {json_data}\n\n"


class AgentService:
    """Service for managing agents"""
    
    def __init__(self):
        """Initialize the agent service"""
        self.core_agent = None
        self.core_agent_config = {"configurable": {"thread_id": "main"}}
        self.agents = {}
        self.agent_states = {}
        
        # Create configs directory if it doesn't exist
        self.configs_dir = os.path.join(os.getcwd(), "configs")
        if not os.path.exists(self.configs_dir):
            os.makedirs(self.configs_dir)
        
        # Initialize core agent
        self.is_initialized = False
    
    async def initialize_core_agent(self) -> None:
        """
        Initialize the core agent.
        This method should be called once before using the core agent.
        """
        logger.info("Initializing core agent")
        self.core_agent = await generate_core_agent()
        self.is_initialized = True
        logger.info("Core agent initialized successfully")
    
    async def check_initialization(self) -> None:
        """
        Check if the agent service is initialized.
        Raises an exception if not initialized.
        """
        if not self.is_initialized:
            logger.error("Agent service not initialized")
            raise ValueError("Agent service not initialized. Call initialize_core_agent() first.")
    
    async def _stream_agent_response(
        self, 
        agent, 
        message: str, 
        config: Optional[Dict[str, Any]] = None,
        on_complete: Optional[Callable] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generic method to stream responses from any agent.
        
        Args:
            agent: The agent to stream from
            message: The message to send to the agent
            config: Optional configuration for the agent
            on_complete: Optional callback function to run on completion
            
        Yields:
            Formatted SSE events
        """
        try:
            # Initial state event
            yield await format_sse_event("state", {"status": "starting", "message": "Starting agent processing"})
            
            # Prepare the message
            messages = [HumanMessage(content=message)]
            
            # Stream from the agent using updates mode
            stream_generator = agent.astream(
                {"messages": messages},
                config,
                stream_mode="updates"
            )
            
            # Process the generator with async for
            async for chunk in stream_generator:
                for node_name, updates in chunk.items():
                    step_data = {
                        "node": node_name,
                        "updates": updates,
                        "timestamp": time.time()
                    }
                    yield await format_sse_event("step", step_data)
            
            # Get final result
            if on_complete:
                final_result = await on_complete(agent, message, config)
                yield await format_sse_event("complete", final_result)
            
        except Exception as e:
            # Error event
            error_data = {
                "status": "error",
                "error": str(e)
            }
            yield await format_sse_event("error", error_data)
            raise
    
    async def send_message_to_core(self, message: str) -> Dict[str, Any]:
        """
        Send a message to the core agent and get a response.
        
        Args:
            message: The message to send
            
        Returns:
            Dictionary with agent response and state
        """
        await self.check_initialization()
        
        logger.info(f"Sending message to core agent: {message[:50]}...")
        try:
            user_message = HumanMessage(content=message)
            result = await self.core_agent.ainvoke(user_message)
            logger.info("Received response from core agent")
            
            # Get final state
            final_state = self.core_agent.acall_state
            
            return {
                "message": result.content,
                "state": {
                    "planned_step": str(final_state.values.get('planned_step', 'None')),
                    "blueprint": final_state.values.get('agent_blueprint', 'No blueprint yet'),
                    "agent_config": _make_json_serializable(final_state.values.get('agent_config', None))
                }
            }
        except Exception as e:
            logger.error(f"Error sending message to core agent: {str(e)}", exc_info=True)
            raise
    
    async def stream_message_to_core(self, message: str, on_complete: Optional[Callable] = None) -> AsyncGenerator[str, None]:
        """
        Stream the response from the core agent with updates for each step
        
        Args:
            message: The message to send
            on_complete: Optional callback for when streaming is complete
            
        Yields:
            Server-sent events with step updates and final state
        """
        await self.check_initialization()
        
        logger.info(f"Streaming message to core agent: {message[:50]}...")
        
        try:
            # Set up input
            user_message = HumanMessage(content=message)
            
            # Use invoke_with_stream_mode
            stream_generator = await self.core_agent.ainvoke_streaming(
                user_message,
                config={
                    "run_name": f"Core agent conversation {time.time()}",
                    "recursion_limit": 25,
                },
                stream_mode="updates"
            )
            
            # Process the generator with async for
            async for chunk in stream_generator:
                for node_name, updates in chunk.items():
                    logger.debug(f"Processing step: {node_name}")
                    step_data = {
                        "id": f"{node_name}-{time.time()}",
                        "node": node_name,
                        "updates": updates,
                        "timestamp": time.time()
                    }
                    yield await format_sse_event("step", step_data)
            
            # Get final result
            if on_complete:
                result = on_complete()
            else:
                # Get final state 
                final_state = self.core_agent.acall_state
                logger.info("Core agent processing completed")
                
                # Return final state
                yield await format_sse_event("state", {
                    "planned_step": str(final_state.values.get('planned_step', 'None')),
                    "blueprint": final_state.values.get('agent_blueprint', 'No blueprint yet'),
                    "agent_config": _make_json_serializable(final_state.values.get('agent_config', None))
                })
                
                # Return complete message
                yield await format_sse_event("complete", {
                    "message": final_state.values.get('message', 'Processing complete')
                })
                
        except Exception as e:
            logger.error(f"Error streaming message to core agent: {str(e)}", exc_info=True)
            yield await format_sse_event("error", {"error": str(e)})
    
    async def generate_agent(self) -> Dict[str, Any]:
        """
        Generate a new agent from the core agent's configuration
        
        Returns:
            Dictionary with the generated agent ID and configuration
        """
        await self.check_initialization()
        
        try:
            logger.info("Generating agent from core agent's configuration")
            
            # Get agent config
            state = self.core_agent.acall_state
            agent_config = state.values.get('agent_config')
            
            if not agent_config:
                logger.error("No agent configuration found in core agent state")
                raise ValueError("No agent configuration found in core agent state")
            
            # Generate agent
            agent_id = str(uuid.uuid4())[:8]
            
            # Create the agent from config
            agent = await generate_agent_from_config(agent_config)
            
            # Store the agent
            self.agents[agent_id] = {
                "agent": agent,
                "config": agent_config,
            }
            
            logger.info(f"Agent generated successfully with ID: {agent_id}")
            
            return {
                "agent_id": agent_id,
                "config": _make_json_serializable(agent_config)
            }
        except Exception as e:
            logger.error(f"Error generating agent: {str(e)}", exc_info=True)
            raise
    
    async def _on_core_stream_complete(self, agent, message, config):
        """Callback for when core agent streaming is complete"""
        # Get final state
        final_state = agent.get_state(config)
        
        # Extract relevant information from final state
        agent_config = final_state.values.get('agent_config')
        
        if agent_config:
            self._save_config_to_file(agent_config)
        
        agent_config_dict = self._get_serializable_config(agent_config) if agent_config else None
        
        # Final result event
        return {
            "status": "complete",
            "message": final_state.values['messages'][-1].content if final_state.values.get('messages') else "",
            "state": {
                "messages": [
                    {"role": self._get_message_role(msg), "content": msg.content} 
                    for msg in final_state.values['messages']
                ] if final_state.values.get('messages') else [],
                "agent_blueprint": final_state.values.get('agent_blueprint', ''),
                "has_agent_config": agent_config is not None,
                "planned_step": str(final_state.values.get('planned_step', 'None')),
                "agent_config": agent_config_dict
            }
        }
    
    async def stream_message_to_core(self, message: str) -> AsyncGenerator[str, None]:
        """
        Stream the response from the core agent with updates for each step
        """
        if not self.core_agent:
            await self.initialize_core_agent()
        
        async for event in self._stream_agent_response(
            self.core_agent, 
            message, 
            self.core_agent_config,
            self._on_core_stream_complete
        ):
            yield event
    
    def _get_serializable_config(self, config):
        """Convert config to a serializable format"""
        if hasattr(config, 'model_dump'):  # Pydantic v2
            return config.model_dump()
        elif hasattr(config, 'dict'):      # Pydantic v1
            return config.dict()
        else:                              # Already a dict
            return config
    
    async def generate_agent_from_core(self) -> Dict[str, Any]:
        """Generate a new agent from the core agent's config"""
        if not self.core_agent:
            await self.initialize_core_agent()
        
        # Get the state from the core agent
        state = self.core_agent.get_state(self.core_agent_config)
        
        # Check if we have an agent config
        agent_config = state.values.get('agent_config')
        if not agent_config:
            return {"error": "No agent configuration available. Please complete the conversation with the core agent first."}
        
        # Generate a unique ID for this agent
        agent_id = str(uuid.uuid4())
        
        # Generate the agent
        agent = await generate_agent_from_config(agent_config)
        
        # Save the config to a file with the agent ID
        self._save_config_to_file(agent_config, agent_id)
        
        # Store the agent
        self.agents[agent_id] = agent
        
        # Initialize agent state
        self.agent_states[agent_id] = {
            "messages": []
        }
        
        return {
            "agent_id": agent_id,
            "message": "Agent generated successfully! You can now communicate with it."
        }
    
    async def _generate_agent_with_steps(self, dummy_message=None):
        """
        Generate an agent with step updates for streaming.
        The dummy_message parameter is not used but required for the streaming interface.
        """
        # Get the state from the core agent
        state = self.core_agent.get_state(self.core_agent_config)
        
        # Check if we have an agent config
        agent_config = state.values.get('agent_config')
        if not agent_config:
            raise ValueError("No agent configuration available. Please complete the conversation with the core agent first.")
        
        # Generate a unique ID for this agent
        agent_id = str(uuid.uuid4())
        
        # Simulate steps for streaming
        # Step 1: Preparing config
        await asyncio.sleep(0.2)
        yield "preparing_config", {"message": "Preparing agent configuration"}
        
        # Step 2: Generating agent
        await asyncio.sleep(0.2)
        yield "generating_agent", {"message": "Generating agent graph from configuration"}
        
        # Generate the agent
        agent = await generate_agent_from_config(agent_config)
        
        # Step 3: Saving config
        await asyncio.sleep(0.2)
        yield "saving_config", {"message": "Saving agent configuration"}
        
        # Save the config to a file with the agent ID
        self._save_config_to_file(agent_config, agent_id)
        
        # Store the agent
        self.agents[agent_id] = agent
        
        # Initialize agent state
        self.agent_states[agent_id] = {
            "messages": []
        }
        
        # Yield the agent_id as the final step instead of returning it
        yield "complete", agent_id
    
    async def _on_generate_agent_complete(self, agent, message, config):
        """Callback for when agent generation is complete"""
        # The agent_id is returned from the _generate_agent_with_steps generator
        agent_id = message
        
        return {
            "status": "complete",
            "agent_id": agent_id,
            "message": "Agent generated successfully! You can now communicate with it."
        }
    
    async def stream_generate_agent_from_core(self) -> AsyncGenerator[str, None]:
        """
        Stream the agent generation process with updates for each step
        """
        try:
            if not self.core_agent:
                await self.initialize_core_agent()
                yield await format_sse_event("state", {"status": "initialized", "message": "Core agent initialized"})
            
            # Get the state from the core agent
            state = self.core_agent.get_state(self.core_agent_config)
            
            # Check if we have an agent config
            agent_config = state.values.get('agent_config')
            if not agent_config:
                yield await format_sse_event("error", {
                    "status": "error", 
                    "error": "No agent configuration available. Please complete the conversation with the core agent first."
                })
                return
            
            # Custom streaming for agent generation since it's not a standard LangGraph streaming operation
            yield await format_sse_event("state", {"status": "configuring", "message": "Configuring agent from blueprint"})
            
            # Create a generator that yields steps
            async for step_name, step_data in self._generate_agent_with_steps():
                yield await format_sse_event("step", {
                    "node": step_name,
                    "updates": step_data,
                    "timestamp": time.time()
                })
            
            # We don't have a final agent_id here since it's generated in the steps
            # So we'll get it from the last step
            agent_id = list(self.agents.keys())[-1]
            
            # Final success event
            yield await format_sse_event("complete", {
                "status": "complete",
                "agent_id": agent_id,
                "message": "Agent generated successfully! You can now communicate with it."
            })
            
        except Exception as e:
            # Error event
            yield await format_sse_event("error", {
                "status": "error",
                "error": str(e)
            })
            raise
    
    async def send_message_to_agent(self, agent_id: str, message: str) -> Dict[str, Any]:
        """
        Send a message to a specific agent
        
        Args:
            agent_id: The ID of the agent
            message: The message to send
            
        Returns:
            Dictionary with the agent's response
        """
        if agent_id not in self.agents:
            logger.error(f"Agent not found: {agent_id}")
            raise ValueError(f"Agent not found: {agent_id}")
        
        logger.info(f"Sending message to agent {agent_id}: {message[:50]}...")
        
        try:
            # Get the agent
            agent_data = self.agents[agent_id]
            agent = agent_data["agent"]
            
            # Create HumanMessage
            user_message = HumanMessage(content=message)
            
            # Add to agent's conversation history
            if "messages" not in agent_data:
                agent_data["messages"] = []
            
            agent_data["messages"].append(user_message)
            
            # Limit message history to last N messages for context window efficiency
            if len(agent_data["messages"]) > MAX_MESSAGES:
                agent_data["messages"] = agent_data["messages"][-MAX_MESSAGES:]
                logger.info(f"Limiting message history to last {MAX_MESSAGES} messages")
            
            # Invoke agent
            logger.info(f"Invoking agent {agent_id}")
            response = await agent.ainvoke(user_message)
            logger.info(f"Received response from agent {agent_id}")
            
            # Add to agent's conversation history
            agent_data["messages"].append(response)
            
            # Return response
            return {
                "message": response.content,
                "agent_id": agent_id
            }
        except Exception as e:
            logger.error(f"Error sending message to agent {agent_id}: {str(e)}", exc_info=True)
            raise
    
    async def stream_message_to_agent(self, agent_id: str, message: str) -> AsyncGenerator[str, None]:
        """
        Stream the response from a specific agent with updates for each step
        
        Args:
            agent_id: The ID of the agent
            message: The message to send
            
        Yields:
            Server-sent events with step updates and final response
        """
        if agent_id not in self.agents:
            logger.error(f"Agent not found: {agent_id}")
            yield await format_sse_event("error", {"error": f"Agent with ID {agent_id} not found"})
            return
        
        logger.info(f"Streaming message to agent {agent_id}: {message[:50]}...")
        
        try:
            # Get the agent
            agent_data = self.agents[agent_id]
            agent = agent_data["agent"]
            
            # Create HumanMessage
            user_message = HumanMessage(content=message)
            
            # Add to agent's conversation history
            if "messages" not in agent_data:
                agent_data["messages"] = []
            
            agent_data["messages"].append(user_message)
            
            # Limit message history to last N messages for context window efficiency
            if len(agent_data["messages"]) > MAX_MESSAGES:
                agent_data["messages"] = agent_data["messages"][-MAX_MESSAGES:]
                logger.info(f"Limiting message history to last {MAX_MESSAGES} messages")
            
            # Set up streaming
            logger.info(f"Setting up streaming for agent {agent_id}")
            stream_generator = await agent.ainvoke_streaming(
                user_message,
                config={
                    "run_name": f"Agent {agent_id} conversation {time.time()}",
                    "recursion_limit": 25,
                },
                stream_mode="updates"
            )
            
            # Process the generator with async for
            async for chunk in stream_generator:
                for node_name, updates in chunk.items():
                    logger.debug(f"Processing step from agent {agent_id}: {node_name}")
                    step_data = {
                        "id": f"{node_name}-{time.time()}",
                        "node": node_name,
                        "updates": updates,
                        "timestamp": time.time()
                    }
                    yield await format_sse_event("step", step_data)
            
            # Get final result from the agent's state
            logger.info(f"Agent {agent_id} processing completed")
            response = agent.acall_state.response
            
            # Add to agent's conversation history
            agent_data["messages"].append(response)
            
            # Return complete message
            yield await format_sse_event("complete", {
                "message": response.content,
                "agent_id": agent_id
            })
            
        except Exception as e:
            logger.error(f"Error streaming message to agent {agent_id}: {str(e)}", exc_info=True)
            yield await format_sse_event("error", {"error": str(e)})
    
    def _get_message_role(self, message):
        """Get the role of a message"""
        if isinstance(message, HumanMessage):
            return "user"
        elif isinstance(message, AIMessage):
            return "assistant"
        elif isinstance(message, SystemMessage):
            return "system"
        else:
            return "unknown"
    
    def _save_config_to_file(self, config, agent_id=None):
        """
        Save the agent config to a file.
        If agent_id is provided, the file will be named with the agent_id.
        Otherwise, a timestamp will be used.
        Only one file will be created per configuration.
        """
        try:
            # Get agent name from config
            agent_name = config.agent_name if hasattr(config, 'agent_name') else config.get('agent_name', 'unnamed')
            agent_name_safe = agent_name.replace(' ', '_')
            
            # Create a filename based on agent_id and agent_name
            if agent_id:
                filename = f"{agent_id}_{agent_name_safe}.json"
            else:
                # Use a timestamp instead of UUID for more readable filenames
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"{agent_name_safe}_{timestamp}.json"
            
            filepath = os.path.join(self.configs_dir, filename)
            
            # Convert config to serializable format
            config_dict = self._get_serializable_config(config)
            
            # Save the config to the file
            with open(filepath, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            print(f"Config saved to {filepath}")
            
            return filepath
            
        except Exception as e:
            print(f"Error saving config: {str(e)}")
            return None


# Singleton instance
agent_service = AgentService() 