from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, status
from fastapi.responses import StreamingResponse
from app.models.agents import ConversationRequest, ConversationResponse, GeneratedAgentResponse
from app.services.agent_service import agent_service
from typing import Dict, Any, AsyncGenerator

router = APIRouter()


@router.post("/core/message", response_model=ConversationResponse)
async def send_message_to_core(request: ConversationRequest):
    """
    Send a message to the core agent
    """
    try:
        result = await agent_service.send_message_to_core(request.message)
        return ConversationResponse(
            message=result["message"],
            state=result["state"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error communicating with core agent: {str(e)}"
        )


@router.get("/core/message/stream")
async def stream_message_to_core(message: str = Query(..., description="Message to send to the core agent")):
    """
    Stream the response from the core agent with updates for each step
    """
    try:
        return StreamingResponse(
            agent_service.stream_message_to_core(message),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error streaming from core agent: {str(e)}"
        )


@router.post("/core/generate", response_model=GeneratedAgentResponse)
async def generate_agent(background_tasks: BackgroundTasks):
    """
    Generate a new agent from the core agent's configuration
    """
    try:
        result = await agent_service.generate_agent_from_core()
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=result["error"]
            )
        return GeneratedAgentResponse(
            agent_id=result["agent_id"],
            message=result["message"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error generating agent: {str(e)}"
        )


@router.get("/core/generate/stream")
async def stream_generate_agent():
    """
    Stream the agent generation process with updates for each step
    """
    try:
        return StreamingResponse(
            agent_service.stream_generate_agent_from_core(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error streaming agent generation: {str(e)}"
        )


@router.post("/{agent_id}/message", response_model=ConversationResponse)
async def send_message_to_agent(agent_id: str, request: ConversationRequest):
    """
    Send a message to a specific agent
    """
    try:
        result = await agent_service.send_message_to_agent(agent_id, request.message)
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=result["error"]
            )
        return ConversationResponse(
            message=result["message"],
            state=result["state"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error communicating with agent: {str(e)}"
        )


@router.get("/{agent_id}/message/stream")
async def stream_message_to_agent(
    agent_id: str, 
    message: str = Query(..., description="Message to send to the agent")
):
    """
    Stream the response from a specific agent with updates for each step
    """
    try:
        return StreamingResponse(
            agent_service.stream_message_to_agent(agent_id, message),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error streaming from agent: {str(e)}"
        )


@router.get("/initialize", response_model=Dict[str, bool])
async def initialize_core_agent(background_tasks: BackgroundTasks):
    """
    Initialize the core agent
    """
    try:
        # Run initialization in the background to not block the request
        background_tasks.add_task(agent_service.initialize_core_agent)
        return {"initializing": True}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error initializing core agent: {str(e)}"
        ) 