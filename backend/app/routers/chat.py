from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import asyncio

from ..services.chat_service import chat_service
from ..services.robot_service import robot_service
from ..config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    message: str
    execute_actions: Optional[bool] = None  # Override setting per request


class ChatResponse(BaseModel):
    response: str
    actions: List[str] = []
    action_results: List[dict] = []


class HistoryMessage(BaseModel):
    role: str
    content: str


class ChatHistoryResponse(BaseModel):
    history: List[HistoryMessage]
    configured: bool


class ConversationRequest(BaseModel):
    message: str
    execute_actions: Optional[bool] = None
    auto_connect: Optional[bool] = None


class ConversationResponse(BaseModel):
    response: str
    actions: List[str] = []
    action_results: List[dict] = []
    robot_connected: bool = False


def extract_actions(text: str) -> tuple[str, List[str]]:
    """Extract bracketed actions from response text."""
    import re
    actions = re.findall(r'\[([^\]]+)\]', text)
    clean_text = re.sub(r'\s*\[[^\]]+\]\s*', ' ', text).strip()
    return clean_text, actions


@router.get("/status")
async def chat_status():
    """Check if chat service is configured and ready."""
    return {
        "configured": chat_service.is_configured(),
        "model": chat_service.model,
        "robot_connected": robot_service.connected,
        "auto_execute_actions": settings.robot_auto_execute_actions
    }


@router.post("/send", response_model=ChatResponse)
async def send_message(chat_message: ChatMessage):
    """Send a message to the robot and get a response."""
    if not chat_message.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    response = await chat_service.chat(chat_message.message)
    clean_response, actions = extract_actions(response)

    # Determine if we should execute actions
    should_execute = chat_message.execute_actions
    if should_execute is None:
        should_execute = settings.robot_auto_execute_actions

    # Execute robot actions if enabled and robot is connected
    action_results = []
    if should_execute and actions and robot_service.connected:
        action_results = await robot_service.execute_actions(actions)

    return ChatResponse(
        response=clean_response,
        actions=actions,
        action_results=action_results
    )


@router.post("/stream")
async def stream_message(chat_message: ChatMessage):
    """Send a message and stream the response."""
    if not chat_message.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Determine if we should execute actions
    should_execute = chat_message.execute_actions
    if should_execute is None:
        should_execute = settings.robot_auto_execute_actions

    async def generate():
        full_response = ""
        async for chunk in chat_service.chat_stream(chat_message.message):
            full_response += chunk
            yield f"data: {json.dumps({'content': chunk})}\n\n"

        # Extract and execute actions after streaming completes
        clean_response, actions = extract_actions(full_response)

        if should_execute and actions and robot_service.connected:
            action_results = await robot_service.execute_actions(actions)
            yield f"data: {json.dumps({'actions': actions, 'action_results': action_results})}\n\n"
        elif actions:
            yield f"data: {json.dumps({'actions': actions})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/conversation", response_model=ConversationResponse)
async def conversation(request: ConversationRequest):
    """
    Complete conversation endpoint that:
    1. Auto-connects to robot if needed
    2. Sends message to Claude
    3. Executes robot actions from response
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Auto-connect to robot if enabled and not connected
    auto_connect = request.auto_connect
    if auto_connect is None:
        auto_connect = settings.robot_auto_connect

    if auto_connect and not robot_service.connected:
        await robot_service.connect()

    # Get Claude's response
    response = await chat_service.chat(request.message)
    clean_response, actions = extract_actions(response)

    # Determine if we should execute actions
    should_execute = request.execute_actions
    if should_execute is None:
        should_execute = settings.robot_auto_execute_actions

    # Execute robot actions
    action_results = []
    if should_execute and actions and robot_service.connected:
        action_results = await robot_service.execute_actions(actions)

    return ConversationResponse(
        response=clean_response,
        actions=actions,
        action_results=action_results,
        robot_connected=robot_service.connected
    )


@router.get("/history", response_model=ChatHistoryResponse)
async def get_history():
    """Get the conversation history."""
    history = chat_service.get_history()
    return ChatHistoryResponse(
        history=[HistoryMessage(**msg) for msg in history],
        configured=chat_service.is_configured()
    )


@router.delete("/history")
async def clear_history():
    """Clear the conversation history."""
    await chat_service.clear_history()
    return {"success": True, "message": "Conversation history cleared"}
