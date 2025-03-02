from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Annotated
from agents_forge.agents_generation.config_schema import AgentConfig
from agents_forge.core_agent.utils.helper_models import NextStep

class AgentCreatorState(BaseModel):
    """State class for AgentCreator agent."""
    messages: Annotated[List[AnyMessage], add_messages]
    agent_bleuprint: str = Field(description="Blueprint for the agent that will be created", default="")
    agent_config: AgentConfig = Field(description="Final configuration for the agent that will be created", default=None)
    planned_step: NextStep = Field(description="Planned step for the agent that will be created", default=None)   