from typing import List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field

class NodeConfig(BaseModel):
    """
    Configuration for a single node in the agent graph.
    
    A node represents a processing step in the agent's workflow. Each node has a unique
    identifier, a type that determines its behavior, and various configuration options.
    """
    id: str = Field(description="Unique identifier for this node")
    type: str = Field(description="Type of node (predefined or custom)")
    objective: str = Field(description="Main objective of this node - what it should accomplish")
    model_name: str = Field( description="Name of the model to use, i prefer gpt-4o-mini")
    temperature: float = Field(description="Temperature parameter for model generation")
    
class EdgeConfig(BaseModel):
    """
    Configuration for an edge in the agent graph.
    
    Edges connect nodes to define the flow of the agent's processing. Each edge has a
    source node and a target node, defining the direction of the flow.
    """
    source: str = Field(description="Source node ID")
    target: str = Field(description="Target node ID")
    
    
class AgentConfig(BaseModel):
    """
    Full configuration for an agent.
    
    This class defines the complete structure of an agent, including its nodes,
    edges, and metadata.
    """
    agent_name: str = Field(description="Name of the agent")
    description: str = Field(description="Description of what this agent does")
    nodes: List[NodeConfig] = Field(description="List of nodes in the agent graph")
    edges: List[EdgeConfig] = Field(description="List of edges connecting the nodes")