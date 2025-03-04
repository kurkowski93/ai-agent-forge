#!/usr/bin/env python3
"""
Agent CLI - Terminal-based application for working with AI agents
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich import print as rprint
from rich.box import ROUNDED
from rich.syntax import Syntax
from dotenv import load_dotenv

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

# Import agent-related modules
try:
    from agents_forge.core_agent.agent import generate_core_agent
    from agents_forge.agents_generation.generator import generate_agent_from_config
    from agents_forge.agents_generation.config_schema import AgentConfig
except ImportError:
    rprint("[bold red]Error:[/bold red] Required modules not found. Make sure you have the agent_forge package installed.")
    sys.exit(1)

# Load environment variables from .env file
load_dotenv(override=True)

# Initialize typer app and rich console
app = typer.Typer(help="CLI application for working with AI agents")
console = Console()

# Configuration
AGENTS_DIR = Path("agent_configs")
DEFAULT_THREAD_ID = "cli_agent_test"

def setup():
    """Set up the application and create necessary directories."""
    os.makedirs(AGENTS_DIR, exist_ok=True)
    rprint("[bold green]✅ Application setup complete[/bold green]")

def safe_object_to_dict(obj):
    """Safely convert an object to a dictionary for display purposes."""
    if obj is None:
        return None
    
    # If it's a simple type, return as is
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    
    # If it's a list, convert each item
    if isinstance(obj, (list, tuple)):
        return [safe_object_to_dict(item) for item in obj]
    
    # If it's a dict, convert values
    if isinstance(obj, dict):
        return {k: safe_object_to_dict(v) for k, v in obj.items()}
    
    # Special handling for common objects
    # Check for NextStep or similar objects
    if hasattr(obj, "name") and hasattr(obj, "args"):
        return {
            "name": obj.name,
            "args": safe_object_to_dict(obj.args) if hasattr(obj.args, "__dict__") else obj.args
        }
    
    # If it has __dict__, use that
    if hasattr(obj, "__dict__"):
        result = {}
        for k, v in obj.__dict__.items():
            # Skip private attributes
            if not k.startswith('_'):
                result[k] = safe_object_to_dict(v)
        return result
    
    # Try to see if it implements the mapping protocol
    try:
        if hasattr(obj, "items"):
            return {k: safe_object_to_dict(v) for k, v in obj.items()}
    except:
        pass
    
    # Otherwise convert to string
    return str(obj)

def display_chunk_info(chunk, response_content=None):
    """Display detailed information about a streaming chunk."""
    # Get the chunk type
    chunk_type = "Message" if hasattr(chunk, "content") and chunk.content else "State Update"
    
    # If it's a message and we're accumulating content, add to the response
    if chunk_type == "Message" and response_content is not None:
        response_content += chunk.content
    
    # Convert to dictionary for display
    chunk_dict = safe_object_to_dict(chunk)
    
    # Render appropriate panel based on chunk type
    if chunk_type == "Message":
        # It's a message from the agent
        rprint(Panel(json.dumps(chunk_dict, indent=2, default=str), 
                    title=f"Message Chunk", 
                    border_style="green"))
    else:
        # Special handling for planned_step if present
        if isinstance(chunk_dict, dict) and "planned_step" in chunk_dict:
            planned_step = chunk_dict.get("planned_step")
            if planned_step:
                rprint(Panel(json.dumps({"planned_step": planned_step}, indent=2, default=str),
                            title="Next Step",
                            border_style="magenta"))
        
        # Show all state updates
        rprint(Panel(json.dumps(chunk_dict, indent=2, default=str), 
                    title=f"State Update Chunk", 
                    border_style="blue"))
    
    # Return the updated response content if we're tracking it
    return response_content

def display_image_in_terminal(image_path):
    """Display an image in the terminal if possible."""
    # Placeholder for terminal image display
    # This will be implementation-specific based on your environment
    try:
        # Try to display the image using ITerm2's imgcat script
        os.system(f"imgcat {image_path}")
        return True
    except:
        return False
    
def display_agent_graph(agent):
    """Generate and display a graph visualization of the agent."""
    # Generate a temporary filename
    graph_path = "temp_graph.png"
    
    # Get the agent to generate its graph visualization
    try:
        agent.save_graph(graph_path)
        rprint(f"[bold blue]📊 Agent graph saved to {graph_path}[/bold blue]")
    except Exception as e:
        rprint(f"[bold red]❌ Error generating agent graph: {e}[/bold red]")
        return
    
    # Try to display the image in the terminal
    if display_image_in_terminal(graph_path):
        rprint("[bold green]✅ Graph displayed![/bold green]")
    else:
        rprint(f"[bold yellow]ℹ️ Unable to display image in terminal. You can view the graph by opening {graph_path}[/bold yellow]")

def initialize_core_agent():
    """Initialize the core agent and return it."""
    with console.status("[bold green]🔄 Initializing core agent...[/bold green]"):
        try:
            # Initialize the agent
            agent = generate_core_agent()
            return agent
        except Exception as e:
            rprint(f"[bold red]❌ Error initializing core agent: {e}[/bold red]")
            sys.exit(1)

def save_agent_config(config: Any, filename: str = "agent_config.json"):
    """Save an agent configuration to a file."""
    # Create the agents directory if it doesn't exist
    os.makedirs(AGENTS_DIR, exist_ok=True)
    
    # If filename doesn't have .json extension, add it
    if not filename.endswith('.json'):
        filename += '.json'
    
    # Construct the full path
    file_path = AGENTS_DIR / filename
    
    try:
        # Convert config to JSON and save to file
        config_json = config.json()
        with open(file_path, 'w') as f:
            f.write(config_json)
        
        rprint(f"[bold green]✅ Agent configuration saved to {file_path}[/bold green]")
        return file_path
    except Exception as e:
        rprint(f"[bold red]❌ Error saving agent configuration: {e}[/bold red]")
        return None

def list_saved_agents():
    """List all saved agent configurations."""
    # Get all JSON files in the agents directory
    agent_files = list(AGENTS_DIR.glob('*.json'))
    
    if not agent_files:
        rprint("[bold yellow]ℹ️ No saved agents found.[/bold yellow]")
        return []
    
    # Create a table to display the agents
    table = Table(title="🤖 Saved Agents", box=ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Size", style="magenta")
    table.add_column("Last Modified", style="yellow")
    
    # Add each agent to the table
    for i, file_path in enumerate(agent_files, 1):
        # Get file information
        name = file_path.stem
        size = f"{file_path.stat().st_size / 1024:.1f} KB"
        modified = time.ctime(file_path.stat().st_mtime)
        
        # Add to table
        table.add_row(str(i), name, size, modified)
    
    # Display the table
    console.print(table)
    
    # Return the list of agent names
    return [file.stem for file in agent_files]

async def load_agent_from_file(filename: str):
    """Load an agent from a saved configuration file."""
    # If filename doesn't have .json extension, add it
    if not filename.endswith('.json'):
        filename += '.json'
    
    # Construct the full path
    file_path = AGENTS_DIR / filename
    
    # Check if the file exists
    if not file_path.exists():
        rprint(f"[bold red]❌ Agent configuration file not found: {file_path}[/bold red]")
        return None
    
    try:
        # Load the configuration from file
        with open(file_path, 'r') as f:
            config_json = f.read()
        
        # Parse the JSON into an AgentConfig object
        agent_config = AgentConfig.parse_raw(config_json)
        
        # Create a loading message
        with console.status(f"[bold green]🔄 Loading agent {agent_config.agent_name}...[/bold green]"):
            # Generate the agent from the configuration
            agent = await generate_agent_from_config(agent_config)
            
            rprint(f"[bold green]✅ Agent {agent_config.agent_name} loaded successfully![/bold green]")
            return agent
    except Exception as e:
        rprint(f"[bold red]❌ Error loading agent: {e}[/bold red]")
        return None

async def chat_with_core_agent():
    """Start a conversation with the core agent."""
    # Initialize the core agent
    rprint("[bold blue]🤖 Initializing Core Agent...[/bold blue]")
    agent = initialize_core_agent()
    display_agent_graph(agent)
    
    config = {"configurable": {"thread_id": DEFAULT_THREAD_ID}}
    messages = []
    
    rprint("[bold green]✅ Agent initialized successfully![/bold green]")
    rprint(Panel.fit(
        "[bold]Chat with Core Agent[/bold]\n\n"
        "Type your messages to interact with the agent.\n"
        "Type [bold cyan]'exit'[/bold cyan] to end the conversation.\n"
        "Type [bold cyan]'generate'[/bold cyan] to generate a custom agent based on the conversation.",
        title="📝 Instructions",
        border_style="blue"
    ))
    
    while True:
        # Get user input
        user_input = Prompt.ask("[bold blue]You[/bold blue]")
        
        if user_input.lower() == "exit":
            rprint("[bold yellow]👋 Exiting conversation.[/bold yellow]")
            break
        
        # Add user message to the list
        messages.append(HumanMessage(content=user_input))
        
        # Handle 'generate' command
        if user_input.lower() == "generate":
            with console.status("[bold green]🔄 Generating agent...[/bold green]"):
                try:
                    # Call agent to generate
                    response = await agent.ainvoke({"messages": messages}, config)
                    
                    # Check if agent_config exists in the state
                    state_snapshot = agent.get_state(config)
                    agent_config = state_snapshot.values.get('agent_config')
                    
                    if agent_config:
                        # Save the configuration
                        save_agent_config(agent_config)
                        
                        # Display agent information
                        rprint(Panel.fit(
                            f"[bold green]✅ Agent generated successfully![/bold green]\n\n"
                            f"[bold]Agent Name:[/bold] {agent_config.agent_name}\n"
                            f"[bold]Description:[/bold] {agent_config.description}\n\n"
                            f"[bold]Structure:[/bold]\n"
                            f"- Nodes: {len(agent_config.nodes)}\n"
                            f"- Edges: {len(agent_config.edges)}\n\n"
                            "You can now test this agent using the 'test' command.",
                            title="🎉 Agent Generated",
                            border_style="green"
                        ))
                        
                        # Ask if the user wants to save the agent with a custom name
                        if Confirm.ask("[bold yellow]Do you want to save this agent with a custom name?[/bold yellow]"):
                            custom_name = Prompt.ask("[bold blue]Enter a name for this agent[/bold blue]")
                            save_agent_config(agent_config, custom_name)
                        
                        # Ask if the user wants to test the agent
                        if Confirm.ask("[bold yellow]Do you want to test this agent now?[/bold yellow]"):
                            new_agent = await generate_agent_from_config(agent_config)
                            display_agent_graph(new_agent)
                            await test_agent(new_agent)
                        
                        break
                    else:
                        rprint("[bold red]❌ Failed to generate agent. Continue the conversation.[/bold red]")
                        # Display the last agent response
                        if response.get("messages") and len(response["messages"]) > 0:
                            ai_message = response["messages"][-1]
                            rprint(f"[bold green]Agent:[/bold green] {ai_message.content}")
                            messages.append(ai_message)
                except Exception as e:
                    rprint(f"[bold red]❌ Error generating agent: {e}[/bold red]")
        else:
            # Process normal message with streaming
            rprint("[bold green]🤖 Agent is thinking...[/bold green]")
            
            try:
                # Use streaming with changes output - just display raw chunks
                response_content = ""
                chunk_count = 0
                
                # Initial message to indicate agent is responding
                rprint("[bold green]Agent (streaming):[/bold green]")
                
                # Stream the response
                for chunk in agent.stream(
                    {"messages": messages}, 
                    config,
                    stream_mode="updates"
                ):
                    try:
                        chunk_count += 1
                        
                        # Add separator between chunks
                        if chunk_count > 1:
                            rprint("[dim]---[/dim]")
                        
                        # Format and print the chunk
                        formatted_chunk = format_chunk(chunk)
                        rprint(formatted_chunk)
                        
                        # Still collect content for message history if it's a message
                        if hasattr(chunk, "content") and chunk.content:
                            response_content += chunk.content
                    except Exception as e:
                        rprint(f"[bold red]❌ Error processing chunk: {e}[/bold red]")
                
                # Final message to indicate streaming is complete
                if chunk_count > 0:
                    rprint("\n--- END OF STREAMING ---\n")
                
                # Save to message history if we got actual content
                if chunk_count > 0:
                    # If we have text content, add it to messages
                    if response_content:
                        ai_message = AIMessage(content=response_content)
                        messages.append(ai_message)
                else:
                    # No streaming chunks received at all
                    rprint("[bold yellow]⚠️ No streaming response received.[/bold yellow]")
                    
            except Exception as e:
                rprint(f"[bold red]❌ Error getting agent response: {e}[/bold red]")

async def test_agent(agent):
    """Test a generated or loaded agent."""
    rprint(Panel.fit(
        "[bold]Test Agent[/bold]\n\n"
        "Type your messages to interact with the agent.\n"
        "Type [bold cyan]'exit'[/bold cyan] to end the test.",
        title="📝 Instructions",
        border_style="blue"
    ))
    
    while True:
        # Get user input
        user_input = Prompt.ask("[bold blue]You[/bold blue]")
        
        if user_input.lower() == "exit":
            rprint("[bold yellow]👋 Exiting test.[/bold yellow]")
            break
        
        # Create message
        user_message = HumanMessage(content=user_input)
        
        # Process the message with streaming
        rprint("[bold green]🤖 Agent is thinking...[/bold green]")
        
        try:
            # Use streaming with changes output - just display raw chunks
            response_content = ""
            chunk_count = 0
            
            # Initial message to indicate agent is responding
            rprint("[bold green]Agent (streaming):[/bold green]")
            
            # Stream the response
            for chunk in agent.stream(
                {"messages": [user_message]},
                stream_mode="updates"
            ):
                try:
                    chunk_count += 1
                    
                    # Add separator between chunks
                    if chunk_count > 1:
                        rprint("[dim]---[/dim]")
                    
                    # Format and print the chunk
                    formatted_chunk = format_chunk(chunk)
                    rprint(formatted_chunk)
                    
                    # Still collect content for message history if it's a message
                    if hasattr(chunk, "content") and chunk.content:
                        response_content += chunk.content
                except Exception as e:
                    rprint(f"[bold red]❌ Error processing chunk: {e}[/bold red]")
            
            # Final message to indicate streaming is complete
            if chunk_count > 0:
                rprint("\n--- END OF STREAMING ---\n")
            
            # No streaming chunks received at all
            if chunk_count == 0:
                rprint("[bold yellow]⚠️ No streaming response received.[/bold yellow]")
                    
        except Exception as e:
            rprint(f"[bold red]❌ Error getting agent response: {e}[/bold red]")

async def test_saved_agent():
    """Load and test a saved agent."""
    agents = list_saved_agents()
    
    if not agents:
        rprint("[bold red]❌ No saved agents found.[/bold red]")
        return
    
    agent_idx = Prompt.ask(
        "[bold blue]Enter the ID of the agent you want to test[/bold blue]", 
        choices=[str(i) for i in range(1, len(agents) + 1)]
    )
    
    agent_name = agents[int(agent_idx) - 1]
    agent = await load_agent_from_file(agent_name)
    
    if agent:
        display_agent_graph(agent)
        await test_agent(agent)

@app.command()
def chat():
    """Start a conversation with the core agent."""
    asyncio.run(chat_with_core_agent())

@app.command()
def test():
    """Load and test a saved agent."""
    asyncio.run(test_saved_agent())

@app.command()
def list():
    """List all saved agent configurations."""
    list_saved_agents()

def format_chunk(chunk):
    """Format chunk data for better readability based on its content."""
    # Get chunk node name if it exists (for better context)
    node_name = None
    try:
        if isinstance(chunk, dict) and len(chunk) == 1:
            # Używamy iter() i next() zamiast list() na keys()
            node_name = next(iter(chunk.keys()))
    except Exception:
        # Ignorujemy błędy przy próbie uzyskania nazwy node'a
        pass
    
    try:
        if isinstance(chunk, dict):
            # Dictionary format for normal agent output
            if node_name:
                return f"[bold yellow]Node: {node_name}[/bold yellow]\n{json.dumps(chunk[node_name], indent=2, default=str)}"
            else:
                return json.dumps(chunk, indent=2, default=str)
        elif hasattr(chunk, "content") and chunk.content:
            # Simple message chunk
            return f"[green]Message: {chunk.content}[/green]"
        else:
            # Try to identify if it's a core agent or custom agent
            if hasattr(chunk, "planned_step") or (hasattr(chunk, "__dict__") and any(isinstance(k, Enum) for k in chunk.__dict__)):
                # Core agent with schema output
                chunk_data = str(chunk)
                # Try to extract node name
                if "{'" in chunk_data and "': {" in chunk_data:
                    parts = chunk_data.split("{'" , 1)
                    if len(parts) > 1:
                        node_parts = parts[1].split("': {", 1)
                        if len(node_parts) > 1:
                            node_name = node_parts[0]
                            chunk_data = f"[bold yellow]Node: {node_name}[/bold yellow]\n{chunk_data}"
                
                # Improve readability of planned_step
                if "planned_step" in chunk_data:
                    chunk_data = chunk_data.replace("<NextStep.", "[bold magenta]").replace(">", "[/bold magenta]")
                # Highlight messages
                if "messages" in chunk_data:
                    chunk_data = chunk_data.replace("AIMessage(content=", "[cyan]AIMessage: [/cyan]")
                    chunk_data = chunk_data.replace("HumanMessage(content=", "[blue]HumanMessage: [/blue]")
                
                return chunk_data
            else:
                # Default fallback
                return str(chunk)
    except Exception as e:
        # W przypadku jakiegokolwiek błędu, po prostu zwróć surowy string
        return f"[yellow]Raw chunk data:[/yellow] {str(chunk)}"

def main():
    """Run the main application."""
    # Print welcome message
    console.print(Panel.fit(
        "[bold]Agent CLI[/bold]\n\n"
        "A command-line interface for working with AI agents.\n\n"
        "Run [bold cyan]agent_cli.py chat[/bold cyan] to start a conversation with the core agent.\n"
        "Run [bold cyan]agent_cli.py test[/bold cyan] to test a saved agent.\n"
        "Run [bold cyan]agent_cli.py list[/bold cyan] to list all saved agents.",
        title="🤖 Welcome to Agent CLI",
        border_style="green"
    ))
    
    setup()
    try:
        app()
    except Exception as e:
        rprint(f"[bold red]❌ Error: {e}[/bold red]")

if __name__ == "__main__":
    main() 