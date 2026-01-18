"""
Voice Control Router.
REST and WebSocket endpoints for voice-controlled Claude Code interaction.
"""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/voice-control", tags=["voice-control"])


class ExecuteCommandRequest(BaseModel):
    """Request body for manual command execution."""
    command: str
    use_claude_code: bool = True


class ExecuteCommandResponse(BaseModel):
    """Response from command execution."""
    success: bool
    output: Optional[str] = None
    response: Optional[str] = None
    error: Optional[str] = None


def _get_voice_control_service():
    """Lazy load voice control service to avoid circular imports."""
    from ..services.voice_control_service import voice_control_service
    return voice_control_service


def _get_claude_code_service():
    """Lazy load Claude Code service."""
    from ..services.claude_code_service import claude_code_service
    return claude_code_service


# ==================== REST Endpoints ====================

@router.post("/start")
async def start_voice_control():
    """Start the voice control system.

    Begins listening for wake words and commands.
    Robot must be connected for audio capture.
    """
    service = _get_voice_control_service()
    result = await service.start()

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return result


@router.post("/stop")
async def stop_voice_control():
    """Stop the voice control system.

    Stops listening and resets the command parser.
    """
    service = _get_voice_control_service()
    result = await service.stop()

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return result


@router.get("/status")
async def get_voice_control_status():
    """Get current status of voice control system.

    Returns:
        Status including state, last command, and service statuses.
    """
    service = _get_voice_control_service()
    return await service.get_status()


@router.post("/execute", response_model=ExecuteCommandResponse)
async def execute_command(request: ExecuteCommandRequest):
    """Manually execute a command (for testing).

    Args:
        command: Natural language command
        use_claude_code: Whether to use Claude Code CLI (default True)

    Returns:
        Command execution result with output and response.
    """
    service = _get_voice_control_service()

    try:
        result = await service.execute_manual_command(
            request.command,
            use_claude_code=request.use_claude_code
        )

        return ExecuteCommandResponse(
            success=result.get("success", False),
            output=result.get("output"),
            response=result.get("response"),
            error=result.get("error")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel")
async def cancel_execution():
    """Cancel the currently executing Claude Code command."""
    claude_code = _get_claude_code_service()
    result = await claude_code.cancel_execution()

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/claude-code/status")
async def get_claude_code_status():
    """Get Claude Code CLI availability status."""
    claude_code = _get_claude_code_service()
    return claude_code.get_status()


# ==================== WebSocket Endpoint ====================

class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


ws_manager = WebSocketManager()


@router.websocket("/ws")
async def voice_control_websocket(websocket: WebSocket):
    """WebSocket for real-time voice control updates.

    Sends events:
        - transcript: Speech-to-text results
        - command: Detected commands
        - response: Claude Code responses
        - status: State changes
        - spoke: TTS output
        - error: Error messages

    Receives commands:
        - start: Start voice control
        - stop: Stop voice control
        - execute: Execute a command
        - status: Request current status
    """
    await ws_manager.connect(websocket)
    service = _get_voice_control_service()

    # Register event callback
    async def event_handler(event):
        try:
            await websocket.send_json({
                "type": event.type,
                "data": event.data,
                "timestamp": event.timestamp
            })
        except Exception:
            pass

    service.add_event_callback(event_handler)

    try:
        # Send initial status
        status = await service.get_status()
        await websocket.send_json({
            "type": "status",
            "data": status,
            "timestamp": None
        })

        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                command = data.get("command", "")

                if command == "start":
                    result = await service.start()
                    await websocket.send_json({
                        "type": "command_result",
                        "command": "start",
                        "data": result
                    })

                elif command == "stop":
                    result = await service.stop()
                    await websocket.send_json({
                        "type": "command_result",
                        "command": "stop",
                        "data": result
                    })

                elif command == "execute":
                    cmd_text = data.get("text", "")
                    use_claude_code = data.get("use_claude_code", True)
                    if cmd_text:
                        result = await service.execute_manual_command(
                            cmd_text,
                            use_claude_code=use_claude_code
                        )
                        await websocket.send_json({
                            "type": "command_result",
                            "command": "execute",
                            "data": result
                        })

                elif command == "status":
                    status = await service.get_status()
                    await websocket.send_json({
                        "type": "status",
                        "data": status
                    })

                elif command == "cancel":
                    claude_code = _get_claude_code_service()
                    result = await claude_code.cancel_execution()
                    await websocket.send_json({
                        "type": "command_result",
                        "command": "cancel",
                        "data": result
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Invalid JSON"}
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[VoiceControl WS] Error: {e}")
    finally:
        service.remove_event_callback(event_handler)
        ws_manager.disconnect(websocket)
