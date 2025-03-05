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
                    title="Message Chunk", 
                    border_style="green"))
    else:
        # Special handling for planned_step if present
        if isinstance(chunk_dict, dict) and "planned_step" in chunk_dict:
            planned_step = chunk_dict.get("planned_step")
            if planned_step:
                rprint(Panel(f"Next step: {planned_step}",
                            title="Next Step",
                            border_style="magenta"))
        
        # Show all state updates in a simplified way
        try:
            # Format for better readability
            formatted_json = json.dumps(chunk_dict, indent=2, default=str)
            rprint(Panel(formatted_json, 
                        title="State Update", 
                        border_style="blue"))
        except Exception as e:
            rprint(f"Error displaying chunk info: {safe_format(str(e))}")
    
    # Return the updated response content if we're tracking it
    return response_content

def safe_format(text):
    """Escape any format specifiers in the text to safely use in f-strings."""
    if not text:
        return text
    # Replace any potential format specifiers
    return str(text).replace("{", "{{").replace("}", "}}")

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
    
    try:
        # Zawsze najpierw próbuj użyć metody get_graph().draw_mermaid_png()
        if hasattr(agent, 'get_graph'):
            graph = agent.get_graph()
            if hasattr(graph, 'draw_mermaid_png'):
                with open(graph_path, 'wb') as f:
                    f.write(graph.draw_mermaid_png())
                rprint(f"[bold blue]📊 Agent graph saved to {graph_path}[/bold blue]")
            else:
                rprint(f"[bold yellow]⚠️ Agent graph object doesn't support draw_mermaid_png[/bold yellow]")
                # Fallback do starej metody
                if hasattr(agent, 'save_graph'):
                    agent.save_graph(graph_path)
                    rprint(f"[bold blue]📊 Agent graph saved to {graph_path} using fallback method[/bold blue]")
                else:
                    rprint(f"[bold yellow]⚠️ This agent type ({type(agent).__name__}) doesn't support graph visualization[/bold yellow]")
                    return False
        # Jeśli agent nie ma metody get_graph, spróbuj użyć save_graph jako fallback
        elif hasattr(agent, 'save_graph'):
            agent.save_graph(graph_path)
            rprint(f"[bold blue]📊 Agent graph saved to {graph_path} using fallback method[/bold blue]")
        else:
            rprint(f"[bold yellow]⚠️ This agent type ({type(agent).__name__}) doesn't support graph visualization[/bold yellow]")
            return False
    except Exception as e:
        rprint(f"[bold red]❌ Error generating agent graph: {e}[/bold red]")
        return False
    
    # Try to display the image in the terminal
    if os.path.exists(graph_path) and display_image_in_terminal(graph_path):
        rprint("[bold green]✅ Graph displayed![/bold green]")
    else:
        rprint(f"[bold yellow]ℹ️ Unable to display image in terminal. You can view the graph by opening {graph_path}[/bold yellow]")
    
    return True

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
        # Convert config to JSON and save to file with pretty formatting
        config_dict = config.model_dump()
        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=4)
        
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
        agent_config = AgentConfig.model_validate_json(config_json)
        
        # Create a loading message
        with console.status(f"[bold green]🔄 Loading agent {agent_config.agent_name}...[/bold green]"):
            # Generate the agent from the configuration
            agent = generate_agent_from_config(agent_config)
            
            rprint(f"[bold green]✅ Agent {agent_config.agent_name} loaded successfully![/bold green]")
            return agent
    except Exception as e:
        rprint(f"[bold red]❌ Error loading agent: {e}[/bold red]")
        return None

def extract_message_content(chunk):
    """Extract actual message content from a streaming chunk."""
    # If it's a direct message chunk
    if hasattr(chunk, "content") and chunk.content:
        return chunk.content
    
    # Handle AIMessage objects directly
    if hasattr(chunk, "__class__") and chunk.__class__.__name__ == "AIMessage":
        if hasattr(chunk, "content"):
            return chunk.content
    
    # If it's a node output with messages
    if isinstance(chunk, dict):
        # Check if there are any message nodes
        for node_name, node_data in chunk.items():
            if isinstance(node_data, dict) and "messages" in node_data:
                messages = node_data.get("messages", [])
                if messages:
                    # Get the last message's content
                    last_message = messages[-1]
                    
                    # Handle AIMessage objects in messages array
                    if hasattr(last_message, "__class__") and last_message.__class__.__name__ == "AIMessage":
                        if hasattr(last_message, "content"):
                            return last_message.content
                    
                    # Handle regular objects with content attribute
                    if hasattr(last_message, "content") and last_message.content:
                        return last_message.content
                    
                    # Process string message format: "content='actual message content' additional_kwargs={} ..."
                    if isinstance(last_message, str) and "content=" in last_message:
                        try:
                            # Extract content between the first set of quotes after content=
                            content_start = last_message.find("content='") + 9  # Length of "content='"
                            if content_start > 9:  # Make sure "content='" was found
                                content_end = last_message.find("'", content_start)
                                if content_end > content_start:
                                    return last_message[content_start:content_end]
                            
                            # Try double quotes if single quotes didn't work
                            content_start = last_message.find('content="') + 9
                            if content_start > 9:
                                content_end = last_message.find('"', content_start)
                                if content_end > content_start:
                                    return last_message[content_start:content_end]
                        except:
                            pass
    
    # For other types of chunks, try to extract from common patterns
    chunk_str = str(chunk)
    if "content='" in chunk_str:
        try:
            # Extract content from a string like: content='message content here'
            content_start = chunk_str.find("content='") + 9
            if content_start > 9:
                content_end = chunk_str.find("'", content_start)
                if content_end > content_start:
                    return chunk_str[content_start:content_end]
        except:
            pass
    
    return None

def should_display_content(chunk):
    """Determine if a chunk contains message content that should be displayed."""
    # If it's a message chunk directly
    if hasattr(chunk, "content") and chunk.content:
        return True
    
    # Check if it's a node chunk with messages
    if isinstance(chunk, dict):
        for node_name, node_data in chunk.items():
            if isinstance(node_data, dict) and "messages" in node_data:
                return True
    
    return False

def get_displayable_content(chunk):
    """Extract only the human-readable content from a chunk, skipping technical details."""
    try:
        # Handle AIMessage objects directly
        if hasattr(chunk, "__class__") and chunk.__class__.__name__ == "AIMessage":
            if hasattr(chunk, "content"):
                return f"[yellow]---CHUNK DIVIDER---[/yellow]\n[green]{safe_format(chunk.content)}[/green]"
            return None
        
        # Handle other types of content
        content = extract_message_content(chunk)
        if content:
            # Handle special case for "Next step: X" messages
            if isinstance(content, str) and content.startswith("Next step:"):
                next_step = content.split(":", 1)[1].strip() if ":" in content else "unknown"
                # Return formatted string for next step
                return f"[yellow]---CHUNK DIVIDER---[/yellow]\n[bold magenta]Next step:[/bold magenta] {safe_format(next_step)}"
            
            # Regular messages
            return f"[yellow]---CHUNK DIVIDER---[/yellow]\n[green]{safe_format(content)}[/green]"
        
        # For the specific case where chunk has "planned_step" directly
        if hasattr(chunk, "planned_step") and chunk.planned_step:
            return f"[yellow]---CHUNK DIVIDER---[/yellow]\n[bold magenta]Next step:[/bold magenta] {safe_format(str(chunk.planned_step))}"
    except Exception as e:
        return f"[yellow]Error formatting content: {safe_format(str(e))}[/yellow]"
    
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
        "Type [bold cyan]'save_config'[/bold cyan] to save a custom agent with your own name and immediately test it.\n"
        "Type [bold cyan]'graph'[/bold cyan] to display the agent's graph visualization.",
        title="📝 Instructions",
        border_style="blue"
    ))
    
    while True:
        # Get user input
        user_input = Prompt.ask("[bold blue]You[/bold blue]")
        
        if user_input.lower() == "exit":
            rprint("[bold yellow]👋 Exiting conversation.[/bold yellow]")
            break
        
        # Handle graph command
        if user_input.lower() == "graph":
            display_agent_graph(agent)
            continue
        
        # Add user message to the list
        messages.append(HumanMessage(content=user_input))
        
        # Handle 'save_config' command
        if user_input.lower() == "save_config":
            try:
                # Check if agent_config exists in the state
                state_snapshot = agent.get_state(config)
                agent_config = state_snapshot.values.get('agent_config')
                
                if agent_config:
                    # Always ask for custom name first
                    custom_name = Prompt.ask("[bold blue]Enter a name for this agent[/bold blue]")
                    
                    # Save the configuration with a clear status
                    with console.status("[bold green]🔄 Saving agent with custom name...[/bold green]") as status:
                        save_agent_config(agent_config, custom_name)
                    
                    # Display agent information
                    rprint(Panel.fit(
                        f"[bold green]✅ Agent saved successfully![/bold green]\n\n"
                        f"[bold]Agent Name:[/bold] {agent_config.agent_name}\n"
                        f"[bold]Description:[/bold] {agent_config.description}\n\n"
                        "Starting agent testing now...",
                        title="🎉 Agent Saved",
                        border_style="green"
                    ))
                    
                    # Generate and test the agent immediately
                    new_agent = generate_agent_from_config(agent_config)
                    display_agent_graph(new_agent)
                    await test_agent(new_agent)
                    
                    # After testing, ask if they want to return to conversation
                    if Confirm.ask("[bold yellow]Return to core agent conversation?[/bold yellow]"):
                        continue
                    else:
                        break
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
                rprint("[bold green]Agent:[/bold green]")
                
                # Stream the response
                final_message = None
                try:
                    for chunk in agent.stream(
                        {"messages": messages}, 
                        config,
                        stream_mode="updates"
                    ):
                        try:
                            chunk_count += 1
                            
                            # Obsługa bezpośrednich obiektów AIMessage z innym wzorcem
                            if hasattr(chunk, "__class__") and chunk.__class__.__name__ == "AIMessage":
                                if hasattr(chunk, "content"):
                                    # Bezpośrednio wyświetl zawartość AIMessage
                                    rprint(f"[yellow]---CHUNK DIVIDER---[/yellow]\n[green]{safe_format(chunk.content)}[/green]")
                                    # Zapisz do final_message
                                    final_message = chunk.content
                                    # Dodaj do całkowitej zawartości odpowiedzi
                                    response_content += chunk.content
                                    continue
                            
                            # Standardowa obsługa dla innych typów chunków    
                            # Get content for display
                            display_content = get_displayable_content(chunk)
                            if display_content:
                                # Use rprint instead of print to properly render Rich formatting tags
                                rprint(display_content)
                            
                            # Extract message content from the chunk for final message
                            message_content = extract_message_content(chunk)
                            if message_content:
                                final_message = message_content
                            
                            # Still collect content for message history if it's a message
                            if hasattr(chunk, "content") and chunk.content:
                                response_content += chunk.content
                        except Exception as e:
                            rprint(f"[red]Error processing chunk: {safe_format(str(e))}[/red]")
                except Exception as e:
                    rprint(f"[red]Error during streaming: {safe_format(str(e))}[/red]")
                
                # Final message to indicate streaming is complete
                if chunk_count > 0:
                    rprint("\n[dim]--- END OF STREAMING ---[/dim]\n")
                
                # No streaming chunks received at all
                if chunk_count == 0:
                    rprint("[bold yellow]⚠️ No streaming response received.")
                
                # Save to message history if we got actual content
                if response_content:
                    ai_message = AIMessage(content=response_content)
                    messages.append(ai_message)
            except Exception as e:
                rprint(f"Error getting agent response: {str(e)}")

async def test_agent(agent):
    """Test a generated or loaded agent."""
    # Initialize list to store conversation history
    messages = []
    
    rprint(Panel.fit(
        "[bold]Test Agent[/bold]\n\n"
        "Type your messages to interact with the agent.\n"
        "Type [bold cyan]'exit'[/bold cyan] to end the test.\n"
        "Type [bold cyan]'graph'[/bold cyan] to display the agent's graph visualization.",
        title="📝 Instructions",
        border_style="blue"
    ))
    
    while True:
        # Get user input
        user_input = Prompt.ask("[bold blue]You[/bold blue]")
        
        if user_input.lower() == "exit":
            rprint("[bold yellow]👋 Exiting test.[/bold yellow]")
            break
        
        # Handle graph command
        if user_input.lower() == "graph":
            display_agent_graph(agent)
            continue
        
        # Create message
        user_message = HumanMessage(content=user_input)
        # Add to history
        messages.append(user_message)
        
        # Process the message with streaming
        rprint("[bold green]🤖 Agent is thinking...[/bold green]")
        
        try:
            # Use streaming with changes output - just display raw chunks
            response_content = ""
            chunk_count = 0
            
            # Initial message to indicate agent is responding
            rprint("[bold green]Agent:[/bold green]")
            
            # Stream the response
            final_message = None
            try:
                # Use full message history instead of just the last message
                for chunk in agent.stream(
                    {"messages": messages},
                    stream_mode="updates"
                ):
                    try:
                        chunk_count += 1
                        
                        # Obsługa bezpośrednich obiektów AIMessage z innym wzorcem
                        if hasattr(chunk, "__class__") and chunk.__class__.__name__ == "AIMessage":
                            if hasattr(chunk, "content"):
                                # Bezpośrednio wyświetl zawartość AIMessage
                                rprint(f"[yellow]---CHUNK DIVIDER---[/yellow]\n[green]{safe_format(chunk.content)}[/green]")
                                # Zapisz do final_message
                                final_message = chunk.content
                                # Dodaj do całkowitej zawartości odpowiedzi
                                response_content += chunk.content
                                continue
                        
                        # Standardowa obsługa dla innych typów chunków    
                        # Get content for display
                        display_content = get_displayable_content(chunk)
                        if display_content:
                            # Use rprint instead of print to properly render Rich formatting tags
                            rprint(display_content)
                        
                        # Extract message content from the chunk for final message
                        message_content = extract_message_content(chunk)
                        if message_content:
                            final_message = message_content
                        
                        # Still collect content for message history if it's a message
                        if hasattr(chunk, "content") and chunk.content:
                            response_content += chunk.content
                    except Exception as e:
                        rprint(f"[red]Error processing chunk: {safe_format(str(e))}[/red]")
            except Exception as e:
                rprint(f"[red]Error during streaming: {safe_format(str(e))}[/red]")
            
            # Final message to indicate streaming is complete
            if chunk_count > 0:
                rprint("\n[dim]--- END OF STREAMING ---[/dim]\n")
            
            # No streaming chunks received at all
            if chunk_count == 0:
                rprint("[bold yellow]⚠️ No streaming response received.")
            
            # Save to message history if we got actual content
            if response_content:
                ai_message = AIMessage(content=response_content)
                messages.append(ai_message)
        except Exception as e:
            rprint(f"Error getting agent response: {str(e)}")

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

@app.command(name="list")
def list_agents():
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
                return f"[bold yellow]Node: {safe_format(node_name)}[/bold yellow]\n{json.dumps(chunk[node_name], indent=2, default=str)}"
            else:
                return json.dumps(chunk, indent=2, default=str)
        elif hasattr(chunk, "content") and chunk.content:
            # Simple message chunk
            return f"[green]Message: {safe_format(chunk.content)}[/green]"
        else:
            # Try to identify if it's a core agent or custom agent
            if hasattr(chunk, "planned_step") or (hasattr(chunk, "__dict__") and any(isinstance(k, Enum) for k in chunk.__dict__)):
                # Core agent with schema output
                chunk_data = safe_format(str(chunk))
                
                # Simplify formatting to improve compatibility with different terminals
                if "planned_step" in chunk_data:
                    chunk_data = chunk_data.replace("NextStep.", "NEXT STEP: ")
                
                if "messages" in chunk_data:
                    chunk_data = chunk_data.replace("AIMessage(content=", "AI: ")
                    chunk_data = chunk_data.replace("HumanMessage(content=", "Human: ")
                
                return chunk_data
            else:
                # Default fallback
                return safe_format(str(chunk))
    except Exception as e:
        # W przypadku jakiegokolwiek błędu, po prostu zwróć surowy string
        return f"Raw chunk data: {safe_format(str(chunk))}"

def main():
    """Run the main application."""
    # Print welcome message with simpler formatting
    console.print("\n=== Agent CLI ===\n")
    console.print("A command-line interface for working with AI agents.\n")
    console.print("Commands:")
    console.print("- agent_cli.py chat : Start a conversation with the core agent")
    console.print("- agent_cli.py test : Test a saved agent")
    console.print("- agent_cli.py list : List all saved agents")
    console.print("\n" + "=" * 50 + "\n")
    
    setup()
    try:
        app()
    except Exception as e:
        rprint(f"Error: {safe_format(str(e))}")

if __name__ == "__main__":
    main() 