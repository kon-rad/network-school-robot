from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..services.robot_service import robot_service

router = APIRouter(prefix="/api/robot", tags=["robot"])


class ConnectRequest(BaseModel):
    connection_mode: str = "auto"


class StatusResponse(BaseModel):
    connected: bool
    connection_mode: str
    last_heartbeat: Optional[str]
    robot_info: Optional[dict]
    imu_data: Optional[dict]


class ActionResponse(BaseModel):
    success: bool
    message: str
    connection_mode: Optional[str] = None


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Get current robot connection status and info."""
    return await robot_service.get_status()


@router.post("/connect", response_model=ActionResponse)
async def connect_robot(request: ConnectRequest = None):
    """Initiate connection to the Reachy Mini robot."""
    mode = request.connection_mode if request else "auto"
    result = await robot_service.connect(connection_mode=mode)
    return result


@router.post("/disconnect", response_model=ActionResponse)
async def disconnect_robot():
    """Disconnect from the Reachy Mini robot."""
    result = await robot_service.disconnect()
    return result


@router.get("/info")
async def get_robot_info():
    """Get detailed robot information."""
    status = await robot_service.get_status()
    if not status["connected"]:
        raise HTTPException(status_code=400, detail="Robot not connected")
    return status["robot_info"]
