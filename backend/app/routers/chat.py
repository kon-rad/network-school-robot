from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json

from ..services.chat_service import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    actions: List[str] = []


class HistoryMessage(BaseModel):
    role: str
    content: str


class ChatHistoryResponse(BaseModel):
    history: List[HistoryMessage]
    configured: bool


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
        "model": chat_service.model
    }


@router.post("/send", response_model=ChatResponse)
async def send_message(chat_message: ChatMessage):
    """Send a message to the robot and get a response."""
    if not chat_message.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    response = await chat_service.chat(chat_message.message)
    clean_response, actions = extract_actions(response)

    return ChatResponse(response=clean_response, actions=actions)


@router.post("/stream")
async def stream_message(chat_message: ChatMessage):
    """Send a message and stream the response."""
    if not chat_message.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    async def generate():
        async for chunk in chat_service.chat_stream(chat_message.message):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
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
    chat_service.clear_history()
    return {"success": True, "message": "Conversation history cleared"}
