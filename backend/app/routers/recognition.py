from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import json

from ..services.person_recognition_service import person_recognition_service

router = APIRouter(prefix="/api/recognition", tags=["recognition"])


class TagPersonRequest(BaseModel):
    name: str
    image_base64: str
    description: Optional[str] = ""


class RecognizeRequest(BaseModel):
    image_base64: str


class InteractionRequest(BaseModel):
    person_id: str
    interaction_type: str
    notes: Optional[str] = ""


@router.get("/status")
async def get_status():
    """Get recognition service status."""
    return {
        "configured": person_recognition_service.is_configured(),
        "known_people_count": len(person_recognition_service._known_people)
    }


@router.post("/detect")
async def detect_faces(request: RecognizeRequest):
    """Detect faces in an image."""
    return await person_recognition_service.detect_faces(request.image_base64)


@router.post("/recognize")
async def recognize_people(request: RecognizeRequest):
    """Recognize and describe people in an image using AI."""
    return await person_recognition_service.recognize_people(request.image_base64)


@router.post("/live")
async def live_recognize():
    """Capture from robot camera and recognize people."""
    return await person_recognition_service.live_recognize()


@router.post("/tag")
async def tag_person(request: TagPersonRequest):
    """Tag/register a person with their face."""
    return await person_recognition_service.tag_person(
        name=request.name,
        image_base64=request.image_base64,
        description=request.description
    )


@router.get("/people")
async def get_people():
    """Get list of all tagged people."""
    return await person_recognition_service.get_people()


@router.delete("/people/{person_id}")
async def remove_person(person_id: str):
    """Remove a tagged person."""
    return await person_recognition_service.remove_person(person_id)


@router.post("/interaction")
async def log_interaction(request: InteractionRequest):
    """Log an interaction with a person."""
    return await person_recognition_service.log_interaction(
        person_id=request.person_id,
        interaction_type=request.interaction_type,
        notes=request.notes
    )


# WebSocket for live recognition stream
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/ws/live")
async def websocket_live_recognition(websocket: WebSocket):
    """WebSocket endpoint for continuous live recognition."""
    await manager.connect(websocket)

    try:
        # Send initial status
        await websocket.send_json({
            "type": "connected",
            "message": "Live recognition stream started"
        })

        while True:
            # Wait for command from client
            data = await websocket.receive_json()

            if data.get("command") == "recognize":
                # Perform live recognition
                result = await person_recognition_service.live_recognize()
                await websocket.send_json({
                    "type": "recognition_result",
                    "data": result
                })

            elif data.get("command") == "continuous":
                # Start continuous recognition
                interval = data.get("interval", 2.0)  # Default 2 seconds
                duration = data.get("duration", 30)  # Default 30 seconds

                for _ in range(int(duration / interval)):
                    result = await person_recognition_service.live_recognize()
                    await websocket.send_json({
                        "type": "recognition_result",
                        "data": result
                    })
                    await asyncio.sleep(interval)

                await websocket.send_json({
                    "type": "continuous_complete",
                    "message": "Continuous recognition completed"
                })

            elif data.get("command") == "stop":
                break

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        manager.disconnect(websocket)
