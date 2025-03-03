import os
import json
import uuid
import asyncio
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agents_forge.core_agent.agent import generate_core_agent
from agents_forge.agents_generation.generator import generate_agent_from_config
from agents_forge.agents_generation.config_schema import AgentConfig


def _make_json_serializable(obj):
    """
    Konwertuje obiekty na formaty JSON-serializable.
    """
    if hasattr(obj, "model_dump"):
        # Pydantic v2
        return obj.model_dump()
    elif hasattr(obj, "dict"):
        # Pydantic v1
        return obj.dict()
    elif isinstance(obj, (HumanMessage, AIMessage, SystemMessage)):
        # Serializacja obiektów Message z LangChain
        return {
            "type": obj.__class__.__name__,
            "content": obj.content,
            "additional_kwargs": obj.additional_kwargs
        }
    # Obsługa obiektów Enum lub podobnych
    elif hasattr(obj, "_value_") and hasattr(obj, "_name_"):
        # Zwróć tylko wartość enuma
        return obj._value_
    elif isinstance(obj, dict):
        # Rekurencyjnie konwertuj słowniki
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        # Rekurencyjnie konwertuj listy
        return [_make_json_serializable(item) for item in obj]
    elif hasattr(obj, "__dict__"):
        # Dla innych obiektów próbuj użyć __dict__
        try:
            return _make_json_serializable(obj.__dict__)
        except:
            return str(obj)
    else:
        # Dla pozostałych typów zwróć stringową reprezentację
        return str(obj)

def _normalize_data(data):
    """
    Uniwersalna funkcja normalizująca dane do formatu JSON-serializable.
    Rekurencyjnie przechodzi przez strukturę danych i upraszcza złożone obiekty.
    """
    if isinstance(data, dict):
        # Przetwarzaj rekurencyjnie każdą wartość w słowniku
        return {k: _normalize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        # Przetwarzaj rekurencyjnie każdy element listy
        return [_normalize_data(item) for item in data]
    elif isinstance(data, (int, float, str, bool, type(None))):
        # Podstawowe typy danych nie wymagają przetwarzania
        return data
    elif hasattr(data, "_value_") and hasattr(data, "_name_"):
        # Upraszczanie obiektów enum
        return data._value_
    else:
        # Dla innych typów próbuj je przekształcić na string
        return str(data)


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
    
    async def initialize_core_agent(self):
        """Initialize the core agent"""
        if not self.core_agent:
            self.core_agent = await generate_core_agent()
            return True
        return False
    
    async def send_message_to_core(self, message: str) -> Dict[str, Any]:
        """Send a message to the core agent"""
        if not self.core_agent:
            await self.initialize_core_agent()
        
        # Prepare the messages
        messages = [HumanMessage(content=message)]
        
        # Send to the agent
        response = await self.core_agent.ainvoke(
            {"messages": messages},
            self.core_agent_config
        )
        
        # Get the latest message
        latest_message = response["messages"][-1].content
        
        # Get the agent state
        state = self.core_agent.get_state(self.core_agent_config)
        
        # Get the agent config
        agent_config = state.values.get('agent_config')
        
        # If we have an agent config, save it to a file
        if agent_config:
            self._save_config_to_file(agent_config)
        
        # Convert agent_config to dict if it's a Pydantic model for JSON serialization
        agent_config_dict = None
        if agent_config:
            if hasattr(agent_config, 'model_dump'):  # Pydantic v2
                agent_config_dict = agent_config.model_dump()
            elif hasattr(agent_config, 'dict'):      # Pydantic v1
                agent_config_dict = agent_config.dict()
            else:                                    # Already a dict
                agent_config_dict = agent_config
        
        # Prepare the response
        result = {
            "message": latest_message,
            "state": {
                "messages": [
                    {"role": self._get_message_role(msg), "content": msg.content} 
                    for msg in state.values['messages']
                ],
                "agent_blueprint": state.values.get('agent_blueprint', ''),
                "has_agent_config": agent_config is not None,
                "planned_step": str(state.values.get('planned_step', 'None')),
                "agent_config": agent_config_dict
            }
        }
        
        return result
    
    async def stream_message_to_core(self, message: str) -> AsyncGenerator[str, None]:
        """
        Stream the response from the core agent with updates for each step
        """
        if not self.core_agent:
            await self.initialize_core_agent()
            
        # Prepare the messages
        messages = [HumanMessage(content=message)]
        
        # Stream format for SSE
        async def format_sse_event(event_type: str, data: Any) -> str:
            # Najpierw normalizuj dane do prostszej struktury
            normalized_data = _normalize_data(data)
            # Następnie konwertuj do formatu JSON-serializable
            serializable_data = _make_json_serializable(normalized_data)
            json_data = json.dumps(serializable_data)
            return f"event: {event_type}\ndata: {json_data}\n\n"
        
        # Initial state event
        yield await format_sse_event("state", {"status": "starting", "message": "Starting core agent processing"})
        
        # Stream from the agent using updates mode
        config = self.core_agent_config.copy()
        
        try:
            # Use LangGraph's streaming capabilities
            # Używamy tylko trybu "updates" dla lepszej wydajności
            stream_generator = self.core_agent.astream(
                {"messages": messages},
                config,
                stream_mode="updates"
            )
            
            # Process the generator with async for
            async for chunk in stream_generator:
                # W trybie "updates" otrzymujemy bezpośrednio słownik z node_name i updates
                for node_name, updates in chunk.items():
                    step_data = {
                        "node": node_name,
                        "updates": updates,
                        "timestamp": time.time()
                    }
                    yield await format_sse_event("step", step_data)
            
            # Get final state
            final_state = self.core_agent.get_state(config)
            
            # Extract relevant information from final state
            agent_config = final_state.values.get('agent_config')
            agent_config_dict = None
            if agent_config:
                self._save_config_to_file(agent_config)
                if hasattr(agent_config, 'model_dump'):
                    agent_config_dict = agent_config.model_dump()
                elif hasattr(agent_config, 'dict'):
                    agent_config_dict = agent_config.dict()
                else:
                    agent_config_dict = agent_config
            
            # Final result event
            final_result = {
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
            yield await format_sse_event("complete", final_result)
            
        except Exception as e:
            # Error event
            error_data = {
                "status": "error",
                "error": str(e)
            }
            yield await format_sse_event("error", error_data)
            raise
    
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
    
    async def stream_generate_agent_from_core(self) -> AsyncGenerator[str, None]:
        """
        Stream the agent generation process with updates for each step
        """
        async def format_sse_event(event_type: str, data: Any) -> str:
            # Najpierw normalizuj dane do prostszej struktury
            normalized_data = _normalize_data(data)
            # Następnie konwertuj do formatu JSON-serializable
            serializable_data = _make_json_serializable(normalized_data)
            json_data = json.dumps(serializable_data)
            return f"event: {event_type}\ndata: {json_data}\n\n"
        
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
            
            yield await format_sse_event("state", {"status": "configuring", "message": "Configuring agent from blueprint"})
            
            # Generate a unique ID for this agent
            agent_id = str(uuid.uuid4())
            
            # Stream the agent generation process
            # Note: Since generate_agent_from_config might not have streaming capability internally,
            # we'll provide progress updates for key steps
            
            yield await format_sse_event("step", {
                "node": "preparing_config", 
                "message": "Preparing agent configuration"
            })
            
            # Shorter delay for better responsiveness
            await asyncio.sleep(0.2)
            
            yield await format_sse_event("step", {
                "node": "generating_agent", 
                "message": "Generating agent graph from configuration"
            })
            
            # Generate the agent
            agent = await generate_agent_from_config(agent_config)
            
            yield await format_sse_event("step", {
                "node": "saving_config", 
                "message": "Saving agent configuration"
            })
            
            # Save the config to a file with the agent ID
            self._save_config_to_file(agent_config, agent_id)
            
            # Store the agent
            self.agents[agent_id] = agent
            
            # Initialize agent state
            self.agent_states[agent_id] = {
                "messages": []
            }
            
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
        """Send a message to a specific agent"""
        # Check if the agent exists
        if agent_id not in self.agents:
            return {"error": f"Agent with ID {agent_id} not found"}
        
        agent = self.agents[agent_id]
        
        # Add message to state
        if agent_id not in self.agent_states:
            self.agent_states[agent_id] = {"messages": []}
        
        self.agent_states[agent_id]["messages"].append({"role": "user", "content": message})
        
        # Send message to agent
        response = await agent.ainvoke({"messages": [HumanMessage(content=message)]})
        
        # Extract the response message
        if "messages" in response and len(response["messages"]) > 0:
            latest_message = response["messages"][-1].content
        else:
            latest_message = str(response)
        
        # Add to state
        self.agent_states[agent_id]["messages"].append({"role": "assistant", "content": latest_message})
        
        return {
            "message": latest_message,
            "state": self.agent_states[agent_id]
        }
    
    async def stream_message_to_agent(self, agent_id: str, message: str) -> AsyncGenerator[str, None]:
        """
        Stream the response from a specific agent with updates for each step
        """
        # Stream format for SSE
        async def format_sse_event(event_type: str, data: Any) -> str:
            # Najpierw normalizuj dane do prostszej struktury
            normalized_data = _normalize_data(data)
            # Następnie konwertuj do formatu JSON-serializable
            serializable_data = _make_json_serializable(normalized_data)
            json_data = json.dumps(serializable_data)
            return f"event: {event_type}\ndata: {json_data}\n\n"
        
        try:
            # Check if the agent exists
            if agent_id not in self.agents:
                yield await format_sse_event("error", {
                    "status": "error", 
                    "error": f"Agent with ID {agent_id} not found"
                })
                return
            
            agent = self.agents[agent_id]
            
            # Add message to state
            if agent_id not in self.agent_states:
                self.agent_states[agent_id] = {"messages": []}
            
            self.agent_states[agent_id]["messages"].append({"role": "user", "content": message})
            
            # Initial state event
            yield await format_sse_event("state", {
                "status": "starting", 
                "message": "Starting agent processing"
            })
            
            # Stream from the agent using updates mode only for better performance
            try:
                # Use LangGraph's streaming capabilities
                stream_generator = agent.astream(
                    {"messages": [HumanMessage(content=message)]},
                    stream_mode="updates"
                )
                
                # Process the generator with async for
                async for chunk in stream_generator:
                    # W trybie "updates" otrzymujemy bezpośrednio słownik z node_name i updates
                    for node_name, updates in chunk.items():
                        step_data = {
                            "node": node_name,
                            "updates": updates,
                            "timestamp": time.time()
                        }
                        yield await format_sse_event("step", step_data)
                
                # Get final response
                response = await agent.ainvoke({"messages": [HumanMessage(content=message)]})
                
                # Extract the response message
                if "messages" in response and len(response["messages"]) > 0:
                    latest_message = response["messages"][-1].content
                else:
                    latest_message = str(response)
                
                # Add to state
                self.agent_states[agent_id]["messages"].append({"role": "assistant", "content": latest_message})
                
                # Final result event
                yield await format_sse_event("complete", {
                    "status": "complete",
                    "message": latest_message,
                    "state": self.agent_states[agent_id]
                })
            
            except Exception as e:
                # Error event
                yield await format_sse_event("error", {
                    "status": "error", 
                    "error": str(e)
                })
        except Exception as e:
            # Error event
            yield await format_sse_event("error", {
                "status": "error",
                "error": str(e)
            })
            raise
    
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
        """Save the agent config to a file"""
        try:
            # Create a filename based on agent name or agent_id
            if agent_id:
                # Use dot notation for Pydantic model or dict.get() if it's a dictionary
                agent_name = config.agent_name if hasattr(config, 'agent_name') else config.get('agent_name', 'unnamed')
                filename = f"{agent_id}_{agent_name.replace(' ', '_')}.json"
            else:
                timestamp = uuid.uuid4().hex[:8]
                agent_name = config.agent_name if hasattr(config, 'agent_name') else config.get('agent_name', 'unnamed')
                filename = f"{agent_name.replace(' ', '_')}_{timestamp}.json"
            
            filepath = os.path.join(self.configs_dir, filename)
            
            # Save the config to the file - convert to dict if it's a Pydantic model
            with open(filepath, 'w') as f:
                if hasattr(config, 'model_dump'):  # Pydantic v2
                    json.dump(config.model_dump(), f, indent=2)
                elif hasattr(config, 'dict'):      # Pydantic v1
                    json.dump(config.dict(), f, indent=2)
                else:                              # Already a dict
                    json.dump(config, f, indent=2)
            
            print(f"Config saved to {filepath}")
            
        except Exception as e:
            print(f"Error saving config: {str(e)}")


# Singleton instance
agent_service = AgentService() 