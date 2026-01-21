from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import json
from ..services.robot_service import robot_service
from ..services.voice_tracking_service import voice_tracking_service
from ..services.video_stream_service import video_stream_service

router = APIRouter(prefix="/api/robot", tags=["robot"])


# ==================== REQUEST/RESPONSE MODELS ====================

class ConnectRequest(BaseModel):
    connection_mode: str = "auto"
    host: Optional[str] = None


class StatusResponse(BaseModel):
    connected: bool
    connection_mode: str
    robot_host: Optional[str] = None
    last_heartbeat: Optional[str] = None
    robot_info: Optional[dict] = None
    imu_data: Optional[dict] = None
    audio_status: Optional[dict] = None


class ActionResponse(BaseModel):
    success: bool
    message: str
    connection_mode: Optional[str] = None
    host: Optional[str] = None


class RobotActionRequest(BaseModel):
    action: str


class MultiActionRequest(BaseModel):
    actions: List[str]


class MultiActionResponse(BaseModel):
    results: List[dict]


class HeadMoveRequest(BaseModel):
    x: float = 0
    y: float = 0
    z: float = 0
    roll: float = 0
    duration: float = 1.0
    method: str = "minjerk"


class AntennaMoveRequest(BaseModel):
    left_angle: float = 0
    right_angle: float = 0
    duration: float = 0.5
    method: str = "minjerk"


class BodyRotateRequest(BaseModel):
    yaw_degrees: float = 0
    duration: float = 1.0
    method: str = "minjerk"


class EmotionRequest(BaseModel):
    emotion: str


class WiggleRequest(BaseModel):
    times: int = 3
    angle: float = 30


# ==================== CONNECTION ENDPOINTS ====================

@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Get current robot connection status and info."""
    status = await robot_service.get_status()
    return StatusResponse(**status)


@router.post("/connect", response_model=ActionResponse)
async def connect_robot(request: ConnectRequest = None):
    """Initiate connection to the Reachy Mini robot."""
    mode = request.connection_mode if request else "auto"
    host = request.host if request else None
    result = await robot_service.connect(connection_mode=mode, host=host)
    return ActionResponse(**result)


@router.post("/disconnect", response_model=ActionResponse)
async def disconnect_robot():
    """Disconnect from the Reachy Mini robot."""
    result = await robot_service.disconnect()
    return ActionResponse(**result)


@router.get("/info")
async def get_robot_info():
    """Get detailed robot information."""
    status = await robot_service.get_status()
    if not status["connected"]:
        raise HTTPException(status_code=400, detail="Robot not connected")
    return status["robot_info"]


# ==================== ACTION ENDPOINTS ====================

@router.post("/action", response_model=ActionResponse)
async def execute_action(request: RobotActionRequest):
    """Execute a robot action based on text description."""
    if not request.action.strip():
        raise HTTPException(status_code=400, detail="Action cannot be empty")
    result = await robot_service.execute_action(request.action)
    return ActionResponse(**result)


@router.post("/actions", response_model=MultiActionResponse)
async def execute_actions(request: MultiActionRequest):
    """Execute multiple robot actions sequentially."""
    if not request.actions:
        raise HTTPException(status_code=400, detail="Actions list cannot be empty")
    results = await robot_service.execute_actions(request.actions)
    return MultiActionResponse(results=results)


# ==================== HEAD MOVEMENT ENDPOINTS ====================

@router.post("/head/move", response_model=ActionResponse)
async def move_head(request: HeadMoveRequest):
    """Move the robot's head to a target position."""
    result = await robot_service.move_head(
        x=request.x,
        y=request.y,
        z=request.z,
        roll=request.roll,
        duration=request.duration,
        method=request.method
    )
    return ActionResponse(**result)


@router.post("/head/look-at-user", response_model=ActionResponse)
async def look_at_user():
    """Center the robot's head to look at the user."""
    result = await robot_service.look_at_user()
    return ActionResponse(**result)


@router.post("/head/nod", response_model=ActionResponse)
async def nod(times: int = 2):
    """Nod the head to show agreement."""
    result = await robot_service.nod(times=times)
    return ActionResponse(**result)


@router.post("/head/shake", response_model=ActionResponse)
async def shake_head(times: int = 2):
    """Shake the head to show disagreement."""
    result = await robot_service.shake_head(times=times)
    return ActionResponse(**result)


@router.post("/head/tilt", response_model=ActionResponse)
async def tilt_head(roll: float = 15, duration: float = 0.5):
    """Tilt the head to express curiosity."""
    result = await robot_service.tilt_head(roll=roll, duration=duration)
    return ActionResponse(**result)


# ==================== ANTENNA ENDPOINTS ====================

@router.post("/antennas/move", response_model=ActionResponse)
async def move_antennas(request: AntennaMoveRequest):
    """Move the robot's antennas to target angles (in degrees)."""
    result = await robot_service.move_antennas(
        left_angle=request.left_angle,
        right_angle=request.right_angle,
        duration=request.duration,
        method=request.method
    )
    return ActionResponse(**result)


@router.post("/antennas/wiggle", response_model=ActionResponse)
async def wiggle_antennas(request: WiggleRequest = None):
    """Wiggle the antennas to express happiness."""
    times = request.times if request else 3
    angle = request.angle if request else 30
    result = await robot_service.wiggle_antennas(times=times, angle=angle)
    return ActionResponse(**result)


@router.post("/antennas/raise", response_model=ActionResponse)
async def raise_antennas():
    """Raise both antennas."""
    result = await robot_service.move_antennas(45, 45, duration=0.5)
    return ActionResponse(**result)


@router.post("/antennas/lower", response_model=ActionResponse)
async def lower_antennas():
    """Lower both antennas."""
    result = await robot_service.move_antennas(-30, -30, duration=0.5)
    return ActionResponse(**result)


# ==================== BODY ENDPOINTS ====================

@router.post("/body/rotate", response_model=ActionResponse)
async def rotate_body(request: BodyRotateRequest):
    """Rotate the robot's body to a target yaw angle."""
    result = await robot_service.rotate_body(
        yaw_degrees=request.yaw_degrees,
        duration=request.duration,
        method=request.method
    )
    return ActionResponse(**result)


# ==================== EMOTION ENDPOINTS ====================

@router.post("/emotion", response_model=ActionResponse)
async def express_emotion(request: EmotionRequest):
    """Express an emotion through combined movements."""
    if not request.emotion.strip():
        raise HTTPException(status_code=400, detail="Emotion cannot be empty")
    result = await robot_service.express_emotion(request.emotion)
    return ActionResponse(**result)


# ==================== AUDIO ENDPOINTS ====================

@router.post("/audio/start-recording", response_model=ActionResponse)
async def start_recording():
    """Start recording audio from the robot's microphone."""
    result = await robot_service.start_recording()
    return ActionResponse(**result)


@router.post("/audio/stop-recording", response_model=ActionResponse)
async def stop_recording():
    """Stop recording audio."""
    result = await robot_service.stop_recording()
    return ActionResponse(**result)


@router.post("/audio/start-playing", response_model=ActionResponse)
async def start_playing():
    """Start audio playback."""
    result = await robot_service.start_playing()
    return ActionResponse(**result)


@router.post("/audio/stop-playing", response_model=ActionResponse)
async def stop_playing():
    """Stop audio playback."""
    result = await robot_service.stop_playing()
    return ActionResponse(**result)


@router.post("/audio/stop", response_model=ActionResponse)
async def stop_audio():
    """Stop all audio operations."""
    result = await robot_service.stop_audio()
    return ActionResponse(**result)


@router.get("/audio/voice-direction")
async def get_voice_direction():
    """Get direction of arrival for detected voice."""
    result = await robot_service.get_voice_direction()
    if result is None:
        return {"direction_of_arrival": None, "speech_detected": False}
    return result


# ==================== CAMERA ENDPOINTS ====================

class CaptureResponse(BaseModel):
    success: bool
    message: str
    image_base64: Optional[str] = None
    format: Optional[str] = None


@router.post("/camera/start", response_model=ActionResponse)
async def start_camera():
    """Start the robot's camera stream."""
    result = await robot_service.start_camera()
    return ActionResponse(**result)


@router.post("/camera/stop", response_model=ActionResponse)
async def stop_camera():
    """Stop the robot's camera stream."""
    result = await robot_service.stop_camera()
    return ActionResponse(**result)


@router.post("/camera/capture", response_model=CaptureResponse)
async def capture_image():
    """Capture an image from the robot's camera."""
    result = await robot_service.capture_image()
    return CaptureResponse(**result)


@router.get("/camera/capture")
async def capture_image_get():
    """Capture an image from the robot's camera (GET version)."""
    result = await robot_service.capture_image()
    return result


# ==================== VOICE TRACKING ENDPOINTS ====================

class VoiceTrackingResponse(BaseModel):
    success: bool
    message: str


class VoiceTrackingStatus(BaseModel):
    tracking_enabled: bool
    last_doa: Optional[float] = None
    smoothing_factor: float
    min_movement_threshold: float


class LookAtSpeakerRequest(BaseModel):
    doa: float
    smooth: bool = True


@router.post("/voice-tracking/start", response_model=VoiceTrackingResponse)
async def start_voice_tracking():
    """
    Start voice tracking mode.
    Robot will automatically turn its head towards whoever is speaking.
    """
    result = await voice_tracking_service.start_tracking()
    return VoiceTrackingResponse(**result)


@router.post("/voice-tracking/stop", response_model=VoiceTrackingResponse)
async def stop_voice_tracking():
    """Stop voice tracking mode."""
    result = await voice_tracking_service.stop_tracking()
    return VoiceTrackingResponse(**result)


@router.get("/voice-tracking/status", response_model=VoiceTrackingStatus)
async def get_voice_tracking_status():
    """Get current voice tracking status."""
    status = await voice_tracking_service.get_status()
    return VoiceTrackingStatus(**status)


@router.post("/voice-tracking/look-at-speaker", response_model=ActionResponse)
async def look_at_speaker(request: LookAtSpeakerRequest):
    """
    Manually turn head towards a specific direction.
    DoA (Direction of Arrival): -180 to 180 degrees, 0 = front.
    """
    result = await voice_tracking_service.look_at_speaker(request.doa, request.smooth)
    return ActionResponse(**result)


# ==================== VIDEO STREAMING ENDPOINTS ====================

class VideoStreamConfig(BaseModel):
    target_fps: int = 60
    quality: int = 60
    max_width: int = 640
    max_height: int = 480


@router.get("/video-stream/status")
async def get_video_stream_status():
    """Get current video stream status."""
    return video_stream_service.get_status()


@router.post("/video-stream/configure")
async def configure_video_stream(config: VideoStreamConfig):
    """Configure video stream parameters."""
    video_stream_service.configure(
        target_fps=config.target_fps,
        quality=config.quality,
        max_width=config.max_width,
        max_height=config.max_height
    )
    return {"success": True, "message": "Stream configured", "config": config.model_dump()}


@router.websocket("/video-stream/ws")
async def video_stream_websocket(websocket: WebSocket):
    """WebSocket endpoint for video streaming at high FPS."""
    await websocket.accept()

    # Queue to receive frames
    frame_queue: asyncio.Queue = asyncio.Queue(maxsize=2)

    async def on_frame(frame_data: dict):
        """Callback when a frame is captured."""
        try:
            # Drop old frames if queue is full (keep latest)
            if frame_queue.full():
                try:
                    frame_queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            frame_queue.put_nowait(frame_data)
        except Exception:
            pass

    # Subscribe to frames
    video_stream_service.subscribe(on_frame)

    # Start streaming if not already
    if not video_stream_service.is_streaming:
        await video_stream_service.start_streaming()

    try:
        while True:
            try:
                # Wait for frame with timeout
                frame_data = await asyncio.wait_for(frame_queue.get(), timeout=1.0)

                # Send frame to client
                await websocket.send_json(frame_data)

            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json({"keepalive": True})
            except WebSocketDisconnect:
                break

    except Exception as e:
        print(f"Video stream WebSocket error: {e}")
    finally:
        # Unsubscribe
        video_stream_service.unsubscribe(on_frame)

        # Stop streaming if no more subscribers
        if video_stream_service.subscriber_count == 0:
            await video_stream_service.stop_streaming()
