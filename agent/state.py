from typing import List, Dict, Any, Annotated
from pydantic import BaseModel, Field
from langgraph.graph import MessagesState
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentForgeState(MessagesState):
    """State class for AgentForge agent."""
    agent_instructions: str = Field(description="Instructions for the agent")
    