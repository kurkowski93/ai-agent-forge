#!/usr/bin/env python
"""
Terminal application for interacting with AI agents.
This provides a simple CLI interface for agent generation and conversation.
"""
import asyncio
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Add the root directory to Python path
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

# Import agent service
from backend.app.services.agent_service import AgentService

class TerminalApp:
    """
    Terminal application for interacting with AI agents.
    """
    def __init__(self):
        # Create agent service instance
        self.agent_service = AgentService()
        self.agent_id = None
        
    async def initialize(self):
        """Initialize the core agent"""
        print("Initializing core agent...")
        try:
            await self.agent_service.initialize_core_agent()
            print("Core agent initialized successfully!")
        except Exception as e:
            logger.error(f"Error initializing core agent: {str(e)}")
            print(f"Error: {str(e)}")
            sys.exit(1)

    async def _process_sse_events(self, events_generator):
        """Helper to process server-sent events"""
        async for event in events_generator:
            # Process SSE events format
            if event.startswith('data:'):
                data = event[5:].strip()
                print(f"\nResponse: {data}")
            else:
                # Just in case we get raw data
                print(f"\nResponse: {event}")

    async def generate_agent(self):
        """Generate a new agent by interacting with the core agent"""
        print("\n=== Agent Generation Mode ===")
        print("Send messages to help define the agent. Type 'done' when you're finished.")
        
        # Start the agent generation process
        try:
            # This starts the process
            print("\nStarting agent generation process...")
            await self._process_sse_events(self.agent_service.stream_generate_agent_from_core())
            
            while True:
                user_input = input("\nYou: ")
                
                if user_input.lower() == 'done':
                    print("\nGenerating agent based on your instructions...")
                    
                    # Complete the agent generation
                    result = await self.agent_service.generate_agent_from_core()
                    self.agent_id = result.get("agent_id")
                    
                    print(f"\nAgent generated successfully!")
                    print(f"Agent ID: {self.agent_id}")
                    break
                
                # Send message to core agent
                print("\nSending your message to core agent...")
                await self._process_sse_events(self.agent_service._stream_agent_response(
                    self.agent_service.core_agent, 
                    user_input, 
                    self.agent_service.core_agent_config,
                    self.agent_service._on_core_stream_complete
                ))
        except Exception as e:
            logger.error(f"Error in agent generation: {str(e)}", exc_info=True)
            print(f"\nError: {str(e)}")

    async def chat_with_agent(self):
        """Chat with the generated agent"""
        if not self.agent_id:
            print("No agent has been generated yet.")
            return
        
        print(f"\n=== Chatting with Agent {self.agent_id} ===")
        print("Type 'exit' to end the conversation.")
        
        while True:
            user_input = input("\nYou: ")
            
            if user_input.lower() == 'exit':
                print("\nExiting chat...")
                break
            
            try:
                # Send message to the agent and display the response
                print("\nAgent is thinking...")
                response = await self.agent_service.send_message_to_agent(self.agent_id, user_input)
                print(f"\nAgent: {response['message']}")
            except Exception as e:
                logger.error(f"Error in chat: {str(e)}", exc_info=True)
                print(f"\nError: {str(e)}")

    async def run(self):
        """Run the terminal application"""
        # Ensure OpenAI API key is set
        if "OPENAI_API_KEY" not in os.environ:
            # Try to load from .env file
            env_path = Path(__file__).parent / ".env"
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
            
            if "OPENAI_API_KEY" not in os.environ:
                print("Error: OPENAI_API_KEY environment variable is not set.")
                print("Please set it or provide it in a .env file.")
                sys.exit(1)
        
        # Initialize the core agent
        await self.initialize()
        
        # Display the main menu
        while True:
            print("\n=== AI Agent Terminal ===")
            print("1. Generate a new agent")
            print("2. Chat with the generated agent")
            print("3. Exit")
            
            choice = input("\nSelect an option (1-3): ")
            
            if choice == '1':
                await self.generate_agent()
            elif choice == '2':
                await self.chat_with_agent()
            elif choice == '3':
                print("\nExiting the application...")
                break
            else:
                print("\nInvalid option. Please try again.")

async def main():
    app = TerminalApp()
    await app.run()

if __name__ == "__main__":
    asyncio.run(main()) 