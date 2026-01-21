from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from ..services.personality_service import personality_service

router = APIRouter(prefix="/api/personality", tags=["personality"])


class SetPersonalityRequest(BaseModel):
    personality: str


@router.get("/current")
async def get_current_personality():
    """Get current active personality."""
    current = personality_service.get_current()
    return {
        "personality": personality_service.current_personality,
        "name": current["name"],
        "description": current["description"],
        "inspiration": current.get("inspiration", "")
    }


@router.post("/set")
async def set_personality(request: SetPersonalityRequest):
    """Set the active personality."""
    return personality_service.set_personality(request.personality)


@router.get("/list")
async def list_personalities():
    """List all available personalities."""
    return personality_service.list_personalities()


@router.get("/{personality_id}")
async def get_personality_details(personality_id: str):
    """Get details for a specific personality."""
    if personality_id not in personality_service._personalities:
        return {"success": False, "message": "Personality not found"}

    personality = personality_service._personalities[personality_id]
    return {
        "success": True,
        "id": personality_id,
        "name": personality["name"],
        "description": personality["description"],
        "inspiration": personality.get("inspiration", ""),
        "voice": personality.get("voice", "alloy"),
        "temperature": personality.get("temperature", 0.7)
    }
