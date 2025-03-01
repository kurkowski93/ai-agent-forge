from langgraph.graph import StateGraph, END, START
from .state import AgentForgeState
from .generator import generate_agent_from_config
import os


async def create_agent_from_config(config_path=None):
    """
    Create an agent from a JSON configuration file.
    
    This function is the main entry point for creating agents using AgentForge.
    It loads a configuration file and uses the generator module to build an agent.
    
    Args:
        config_path: Path to the JSON configuration file. If None, uses the example configuration.
        
    Returns:
        A compiled LangGraph agent ready to be executed
    """
    if config_path is None:
        # Use the example configuration if no path is provided
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "example_config.json")
    
    return await generate_agent_from_config(config_path)

