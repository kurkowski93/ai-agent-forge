import json
import importlib
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END, START
from agents_forge.agents_generation.state import AgentForgeState
from agents_forge.agents_generation.node_types import create_node, NodeType
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, create_model, Field
from agents_forge.agents_generation.config_schema import AgentConfig

async def generate_agent_from_config(config_path: str):
    """
    Generate an agent from a JSON configuration file.
    
    This function loads a JSON configuration file, validates it against the AgentConfig schema,
    and builds a LangGraph agent with nodes and edges as specified in the configuration.
    
    Args:
        config_path: Path to the JSON configuration file
        
    Returns:
        A compiled LangGraph agent ready to be executed
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        json.JSONDecodeError: If the configuration file contains invalid JSON
        ValidationError: If the configuration doesn't match the expected schema
    """
    # Load the configuration
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except json.JSONDecodeError:
        raise json.JSONDecodeError(f"Invalid JSON in configuration file: {config_path}")
    
    # Validate the configuration using Pydantic
    config = AgentConfig.model_validate(config_data)
    
    # Initialize state graph
    workflow = StateGraph(AgentForgeState)
    
    # Create and add nodes
    for node_config in config.nodes:
        node_id = node_config.id
        node_type = node_config.type
        
        # Use the entire node_config as the config for the create_node function
        # The specific node creation functions will extract what they need
        node_function = await create_node(node_type, node_config)
        
        # Add the node to the graph
        workflow.add_node(node_id, node_function)
    
    # Add edges
    for edge_config in config.edges:
        source = edge_config.source
        target = edge_config.target
        
        # Handle special cases for START and END
        if source == "START":
            source = START
        if target == "END":
            target = END
        
        workflow.add_edge(source, target)
    
    # Compile the graph
    compiled_agent = workflow.compile()
    
    return compiled_agent
