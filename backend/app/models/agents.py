from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class Message(BaseModel):
    """Message model for the API"""
    role: str  # 'user', 'assistant', 'system'
    content: str


class ConversationRequest(BaseModel):
    """Request model for sending a message to an agent"""
    message: str


class ConversationResponse(BaseModel):
    """Response model for agent messages"""
    message: str
    state: Optional[Dict[str, Any]] = None


class GeneratedAgentResponse(BaseModel):
    """Response model for a generated agent"""
    agent_id: str
    message: str 