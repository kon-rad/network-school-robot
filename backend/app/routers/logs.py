from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc
from typing import Optional
from datetime import datetime
import uuid

from ..database import get_db
from ..models.robot_log import RobotLog
from ..websocket.manager import manager
from ..services.robot_service import robot_service

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("")
async def get_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    level: Optional[str] = None,
    source: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get paginated logs from database."""
    query = select(RobotLog).order_by(desc(RobotLog.timestamp))

    if level:
        query = query.where(RobotLog.level == level.upper())
    if source:
        query = query.where(RobotLog.source == source)

    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "logs": [
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "source": log.source,
                "message": log.message,
                "metadata": log.metadata_
            }
            for log in logs
        ],
        "page": page,
        "limit": limit
    }


@router.delete("")
async def clear_logs(db: AsyncSession = Depends(get_db)):
    """Clear all logs from database."""
    await db.execute(delete(RobotLog))
    await db.commit()
    return {"success": True, "message": "Logs cleared"}


@router.websocket("/stream")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for real-time log streaming."""
    await manager.connect(websocket)

    async def log_callback(log_entry: dict):
        await manager.broadcast(log_entry)

    robot_service.add_log_callback(log_callback)

    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to log stream",
            "timestamp": datetime.utcnow().isoformat()
        })

        while True:
            try:
                data = await websocket.receive_text()
            except WebSocketDisconnect:
                break
    except Exception:
        pass
    finally:
        robot_service.remove_log_callback(log_callback)
        manager.disconnect(websocket)
