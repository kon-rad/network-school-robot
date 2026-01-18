import os
import sys

# Set up GStreamer/GLib library paths for macOS before any gi imports
if sys.platform == "darwin":
    homebrew_lib = "/opt/homebrew/lib"
    homebrew_gst = "/opt/homebrew/opt/gstreamer/lib"
    gst_plugin_path = "/opt/homebrew/lib/gstreamer-1.0"

    # Add library paths
    current_dyld = os.environ.get("DYLD_LIBRARY_PATH", "")
    if homebrew_lib not in current_dyld:
        os.environ["DYLD_LIBRARY_PATH"] = f"{homebrew_lib}:{homebrew_gst}:{current_dyld}".strip(":")

    # Set GStreamer plugin path
    if "GST_PLUGIN_PATH" not in os.environ:
        os.environ["GST_PLUGIN_PATH"] = gst_plugin_path

    # Set GI typelib path for PyGObject
    gi_typelib_path = "/opt/homebrew/lib/girepository-1.0"
    current_gi = os.environ.get("GI_TYPELIB_PATH", "")
    if gi_typelib_path not in current_gi:
        os.environ["GI_TYPELIB_PATH"] = f"{gi_typelib_path}:{current_gi}".strip(":")

import asyncio
import httpx
import numpy as np
import subprocess
from datetime import datetime
from typing import Callable, List, Optional, Any
from ..config import get_settings

settings = get_settings()


def create_head_pose(x: float = 0, y: float = 0, z: float = 0,
                     roll: float = 0, mm: bool = True, degrees: bool = True):
    """Create a head pose target. Wrapper for SDK function."""
    try:
        from reachy_mini.utils import create_head_pose as sdk_create_head_pose
        return sdk_create_head_pose(x=x, y=y, z=z, roll=roll, mm=mm, degrees=degrees)
    except ImportError:
        return {"x": x, "y": y, "z": z, "roll": roll, "mm": mm, "degrees": degrees}


class RobotService:
    def __init__(self):
        self.mini = None
        self.connected = False
        self.connection_mode = settings.robot_connection_mode
        self.robot_host = settings.robot_host
        self.log_callbacks: List[Callable] = []
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._audio_playing = False
        self._audio_recording = False
        self._camera_started = False

    async def connect(self, connection_mode: str = "auto", host: str = None) -> dict:
        """Initialize connection to Reachy Mini robot."""
        try:
            target_host = host or self.robot_host
            await self._log("INFO", "connection", f"Attempting to connect with mode: {connection_mode}, host: {target_host}")

            try:
                from reachy_mini import ReachyMini

                # Try with WebRTC media for camera/audio, fallback to no_media if it fails
                try:
                    await self._log("INFO", "connection", "Attempting connection with WebRTC media...")
                    if connection_mode == "localhost_only":
                        self.mini = ReachyMini(connection_mode="localhost_only", media_backend="webrtc", timeout=20.0)
                    elif connection_mode == "network":
                        self.mini = ReachyMini(connection_mode="network", media_backend="webrtc", timeout=20.0)
                    elif connection_mode == "usb":
                        self.mini = ReachyMini(connection_mode="localhost_only", media_backend="webrtc", timeout=20.0)
                    else:
                        self.mini = ReachyMini(media_backend="webrtc", timeout=20.0)
                    await self._log("INFO", "connection", "WebRTC media connected successfully")
                except Exception as media_error:
                    await self._log("WARN", "connection", f"WebRTC media failed: {media_error}, using no_media")
                    if connection_mode == "localhost_only":
                        self.mini = ReachyMini(connection_mode="localhost_only", media_backend="no_media", timeout=15.0)
                    elif connection_mode == "network":
                        self.mini = ReachyMini(connection_mode="network", media_backend="no_media", timeout=15.0)
                    else:
                        self.mini = ReachyMini(media_backend="no_media", timeout=15.0)

                self.connected = True
                await self._log("INFO", "connection", "Successfully connected to Reachy Mini")

                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

                # Auto-start voice tracking for live head following
                try:
                    from .voice_tracking_service import voice_tracking_service
                    await voice_tracking_service.start_tracking()
                    await self._log("INFO", "connection", "Voice tracking auto-started")
                except Exception as vt_error:
                    await self._log("WARN", "connection", f"Voice tracking auto-start failed: {vt_error}")

                return {
                    "success": True,
                    "message": "Connected to Reachy Mini",
                    "connection_mode": connection_mode,
                    "host": target_host
                }
            except ImportError:
                await self._log("WARN", "connection", "reachy-mini SDK not installed, running in simulation mode")
                self.connected = True
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                return {
                    "success": True,
                    "message": "Running in simulation mode (SDK not installed)",
                    "connection_mode": "simulation"
                }

        except Exception as e:
            await self._log("ERROR", "connection", f"Failed to connect: {str(e)}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "connection_mode": connection_mode
            }

    async def disconnect(self) -> dict:
        """Safely disconnect from the robot."""
        try:
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                self._heartbeat_task = None

            if self.mini:
                # Stop any audio
                await self.stop_audio()
                self.mini = None

            self.connected = False
            await self._log("INFO", "connection", "Disconnected from Reachy Mini")

            return {"success": True, "message": "Disconnected successfully"}
        except Exception as e:
            await self._log("ERROR", "connection", f"Error during disconnect: {str(e)}")
            return {"success": False, "message": f"Disconnect error: {str(e)}"}

    async def get_status(self) -> dict:
        """Get current robot status."""
        status = {
            "connected": self.connected,
            "connection_mode": self.connection_mode,
            "robot_host": self.robot_host,
            "last_heartbeat": datetime.utcnow().isoformat() if self.connected else None,
            "robot_info": None,
            "imu_data": None,
            "audio_status": {
                "playing": self._audio_playing,
                "recording": self._audio_recording
            }
        }

        if self.connected and self.mini:
            try:
                status["robot_info"] = {
                    "mode": "wireless" if hasattr(self.mini, 'imu') else "lite",
                    "sdk_version": "0.1.0",
                    "has_camera": hasattr(self.mini, 'media'),
                    "has_audio": hasattr(self.mini, 'media')
                }

                if hasattr(self.mini, 'imu'):
                    imu = self.mini.imu
                    status["imu_data"] = {
                        "accelerometer": list(imu.get("accelerometer", [])) if isinstance(imu, dict) else None,
                        "gyroscope": list(imu.get("gyroscope", [])) if isinstance(imu, dict) else None,
                        "quaternion": list(imu.get("quaternion", [])) if isinstance(imu, dict) else None,
                    }
            except Exception as e:
                await self._log("WARN", "status", f"Error reading robot info: {str(e)}")

        return status

    def add_log_callback(self, callback: Callable):
        """Register a callback for log events."""
        self.log_callbacks.append(callback)

    def remove_log_callback(self, callback: Callable):
        """Remove a registered log callback."""
        if callback in self.log_callbacks:
            self.log_callbacks.remove(callback)

    async def _log(self, level: str, source: str, message: str, metadata: dict = None):
        """Internal logging that triggers callbacks."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "source": source,
            "message": message,
            "metadata": metadata or {}
        }

        for callback in self.log_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(log_entry)
                else:
                    callback(log_entry)
            except Exception:
                pass

    async def _heartbeat_loop(self):
        """Send periodic heartbeat logs while connected."""
        while self.connected:
            try:
                await self._log("DEBUG", "heartbeat", "Robot heartbeat", {
                    "connected": self.connected,
                    "timestamp": datetime.utcnow().isoformat()
                })
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self._log("ERROR", "heartbeat", f"Heartbeat error: {str(e)}")
                await asyncio.sleep(5)

    # ==================== MOVEMENT METHODS ====================

    async def move_head(self, x: float = 0, y: float = 0, z: float = 0,
                        roll: float = 0, duration: float = 1.0,
                        method: str = "minjerk") -> dict:
        """Move the robot's head to a target position."""
        try:
            await self._log("INFO", "movement", f"Moving head to (x={x}, y={y}, z={z}, roll={roll})")

            if self.mini:
                head_pose = create_head_pose(x=x, y=y, z=z, roll=roll, mm=True, degrees=True)
                self.mini.goto_target(head=head_pose, duration=duration, method=method)
                await asyncio.sleep(duration)
                return {"success": True, "message": f"Head moved to (x={x}, y={y}, z={z})"}
            else:
                await self._log("INFO", "movement", "Simulating head movement")
                await asyncio.sleep(duration)
                return {"success": True, "message": f"Simulated head move to (x={x}, y={y}, z={z})"}

        except Exception as e:
            await self._log("ERROR", "movement", f"Head movement failed: {str(e)}")
            return {"success": False, "message": str(e)}

    async def move_antennas(self, left_angle: float = 0, right_angle: float = 0,
                            duration: float = 0.5, method: str = "minjerk") -> dict:
        """Move the robot's antennas to target angles (in degrees)."""
        try:
            await self._log("INFO", "movement", f"Moving antennas to ({left_angle}, {right_angle}) degrees")

            if self.mini:
                antennas = np.deg2rad([left_angle, right_angle])
                self.mini.goto_target(antennas=antennas, duration=duration, method=method)
                await asyncio.sleep(duration)
                return {"success": True, "message": f"Antennas moved to ({left_angle}, {right_angle})"}
            else:
                await self._log("INFO", "movement", "Simulating antenna movement")
                await asyncio.sleep(duration)
                return {"success": True, "message": f"Simulated antenna move to ({left_angle}, {right_angle})"}

        except Exception as e:
            await self._log("ERROR", "movement", f"Antenna movement failed: {str(e)}")
            return {"success": False, "message": str(e)}

    async def wiggle_antennas(self, times: int = 3, angle: float = 30) -> dict:
        """Wiggle the antennas to express happiness or excitement."""
        try:
            await self._log("INFO", "movement", f"Wiggling antennas {times} times")

            for i in range(times):
                await self.move_antennas(angle, -angle, duration=0.2)
                await self.move_antennas(-angle, angle, duration=0.2)

            await self.move_antennas(0, 0, duration=0.3)
            return {"success": True, "message": f"Antennas wiggled {times} times"}

        except Exception as e:
            await self._log("ERROR", "movement", f"Antenna wiggle failed: {str(e)}")
            return {"success": False, "message": str(e)}

    async def rotate_body(self, yaw_degrees: float = 0, duration: float = 1.0,
                          method: str = "minjerk") -> dict:
        """Rotate the robot's body to a target yaw angle (in degrees)."""
        try:
            await self._log("INFO", "movement", f"Rotating body to {yaw_degrees} degrees")

            if self.mini:
                body_yaw = np.deg2rad(yaw_degrees)
                self.mini.goto_target(body_yaw=body_yaw, duration=duration, method=method)
                await asyncio.sleep(duration)
                return {"success": True, "message": f"Body rotated to {yaw_degrees} degrees"}
            else:
                await self._log("INFO", "movement", "Simulating body rotation")
                await asyncio.sleep(duration)
                return {"success": True, "message": f"Simulated body rotate to {yaw_degrees} degrees"}

        except Exception as e:
            await self._log("ERROR", "movement", f"Body rotation failed: {str(e)}")
            return {"success": False, "message": str(e)}

    async def look_at_user(self) -> dict:
        """Center the robot to look at the user."""
        return await self.move_head(x=0, y=0, z=0, duration=0.8)

    async def nod(self, times: int = 2) -> dict:
        """Nod the head to show agreement or acknowledgment."""
        try:
            await self._log("INFO", "movement", f"Nodding {times} times")

            for i in range(times):
                await self.move_head(z=-15, duration=0.3)
                await self.move_head(z=10, duration=0.3)

            await self.move_head(z=0, duration=0.2)
            return {"success": True, "message": f"Nodded {times} times"}

        except Exception as e:
            await self._log("ERROR", "movement", f"Nod failed: {str(e)}")
            return {"success": False, "message": str(e)}

    async def shake_head(self, times: int = 2) -> dict:
        """Shake head to show disagreement."""
        try:
            await self._log("INFO", "movement", f"Shaking head {times} times")

            for i in range(times):
                await self.move_head(x=-20, duration=0.25)
                await self.move_head(x=20, duration=0.25)

            await self.move_head(x=0, duration=0.2)
            return {"success": True, "message": f"Head shaken {times} times"}

        except Exception as e:
            await self._log("ERROR", "movement", f"Head shake failed: {str(e)}")
            return {"success": False, "message": str(e)}

    async def tilt_head(self, roll: float = 15, duration: float = 0.5) -> dict:
        """Tilt the head to express curiosity."""
        try:
            await self._log("INFO", "movement", f"Tilting head {roll} degrees")
            return await self.move_head(roll=roll, duration=duration)
        except Exception as e:
            await self._log("ERROR", "movement", f"Head tilt failed: {str(e)}")
            return {"success": False, "message": str(e)}

    async def express_emotion(self, emotion: str) -> dict:
        """Express an emotion through combined movements."""
        emotion_lower = emotion.lower()

        try:
            if emotion_lower in ["happy", "excited", "joy"]:
                await self.wiggle_antennas(times=3)
                await self.move_antennas(30, 30, duration=0.3)
                return {"success": True, "message": f"Expressed {emotion}"}

            elif emotion_lower in ["sad", "disappointed"]:
                await self.move_antennas(-20, -20, duration=0.5)
                await self.move_head(z=-10, duration=0.5)
                return {"success": True, "message": f"Expressed {emotion}"}

            elif emotion_lower in ["curious", "interested", "thinking"]:
                await self.tilt_head(roll=15, duration=0.5)
                await self.move_antennas(20, -10, duration=0.3)
                return {"success": True, "message": f"Expressed {emotion}"}

            elif emotion_lower in ["surprised", "shocked"]:
                await self.move_head(z=15, duration=0.3)
                await self.move_antennas(45, 45, duration=0.2)
                return {"success": True, "message": f"Expressed {emotion}"}

            elif emotion_lower in ["confused", "puzzled"]:
                await self.tilt_head(roll=20, duration=0.4)
                await self.shake_head(times=1)
                return {"success": True, "message": f"Expressed {emotion}"}

            elif emotion_lower in ["agreeing", "yes"]:
                await self.nod(times=2)
                return {"success": True, "message": f"Expressed {emotion}"}

            elif emotion_lower in ["disagreeing", "no"]:
                await self.shake_head(times=2)
                return {"success": True, "message": f"Expressed {emotion}"}

            else:
                await self._log("WARN", "emotion", f"Unknown emotion: {emotion}")
                return {"success": False, "message": f"Unknown emotion: {emotion}"}

        except Exception as e:
            await self._log("ERROR", "emotion", f"Emotion expression failed: {str(e)}")
            return {"success": False, "message": str(e)}

    # ==================== AUDIO METHODS ====================

    async def start_recording(self) -> dict:
        """Start recording audio from the robot's microphone."""
        try:
            if self.mini and hasattr(self.mini, 'media'):
                self.mini.media.start_recording()
                self._audio_recording = True
                await self._log("INFO", "audio", "Started audio recording")
                return {"success": True, "message": "Recording started"}
            else:
                await self._log("INFO", "audio", "Simulating audio recording start")
                self._audio_recording = True
                return {"success": True, "message": "Simulated recording started"}
        except Exception as e:
            await self._log("ERROR", "audio", f"Failed to start recording: {str(e)}")
            return {"success": False, "message": str(e)}

    async def stop_recording(self) -> dict:
        """Stop recording audio."""
        try:
            if self.mini and hasattr(self.mini, 'media'):
                self.mini.media.stop_recording()
            self._audio_recording = False
            await self._log("INFO", "audio", "Stopped audio recording")
            return {"success": True, "message": "Recording stopped"}
        except Exception as e:
            await self._log("ERROR", "audio", f"Failed to stop recording: {str(e)}")
            return {"success": False, "message": str(e)}

    async def get_audio_sample(self) -> Optional[np.ndarray]:
        """Get audio sample from microphone."""
        try:
            if self.mini and hasattr(self.mini, 'media') and self._audio_recording:
                return self.mini.media.get_audio_sample()
            return None
        except Exception as e:
            await self._log("ERROR", "audio", f"Failed to get audio sample: {str(e)}")
            return None

    async def start_playing(self) -> dict:
        """Start audio playback."""
        try:
            if self.mini and hasattr(self.mini, 'media'):
                self.mini.media.start_playing()
                self._audio_playing = True
                await self._log("INFO", "audio", "Started audio playback")
                return {"success": True, "message": "Playback started"}
            else:
                self._audio_playing = True
                return {"success": True, "message": "Simulated playback started"}
        except Exception as e:
            await self._log("ERROR", "audio", f"Failed to start playback: {str(e)}")
            return {"success": False, "message": str(e)}

    async def stop_playing(self) -> dict:
        """Stop audio playback."""
        try:
            if self.mini and hasattr(self.mini, 'media'):
                self.mini.media.stop_playing()
            self._audio_playing = False
            await self._log("INFO", "audio", "Stopped audio playback")
            return {"success": True, "message": "Playback stopped"}
        except Exception as e:
            await self._log("ERROR", "audio", f"Failed to stop playback: {str(e)}")
            return {"success": False, "message": str(e)}

    async def push_audio(self, samples: np.ndarray) -> dict:
        """Push audio samples to the speaker."""
        try:
            if self.mini and hasattr(self.mini, 'media') and self._audio_playing:
                self.mini.media.push_audio_sample(samples)
                return {"success": True, "message": "Audio pushed"}
            return {"success": True, "message": "Simulated audio push"}
        except Exception as e:
            await self._log("ERROR", "audio", f"Failed to push audio: {str(e)}")
            return {"success": False, "message": str(e)}

    async def stop_audio(self) -> dict:
        """Stop all audio operations."""
        await self.stop_recording()
        await self.stop_playing()
        return {"success": True, "message": "All audio stopped"}

    async def get_voice_direction(self) -> Optional[dict]:
        """Get direction of arrival for voice via robot API."""
        try:
            # Use robot's REST API for DoA (works without gstreamer)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://{self.robot_host}:8000/api/state/doa",
                    timeout=2.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "direction_of_arrival": data.get("angle"),
                        "speech_detected": data.get("speech_detected", False)
                    }
            return None
        except Exception as e:
            await self._log("ERROR", "audio", f"Failed to get voice direction: {str(e)}")
            return None

    # ==================== CAMERA METHODS ====================

    async def start_camera(self) -> dict:
        """Start the camera stream."""
        try:
            if self.mini and hasattr(self.mini, 'media') and self.mini.media:
                # Try to start camera stream if not already started
                if not self._camera_started:
                    if hasattr(self.mini.media, 'start_camera'):
                        self.mini.media.start_camera()
                        self._camera_started = True
                        await self._log("INFO", "camera", "Camera stream started")
                    elif hasattr(self.mini.media, 'start'):
                        self.mini.media.start()
                        self._camera_started = True
                        await self._log("INFO", "camera", "Media stream started")
                    else:
                        # Camera might auto-start, mark as started
                        self._camera_started = True
                return {"success": True, "message": "Camera started"}
            return {"success": False, "message": "No media available"}
        except Exception as e:
            await self._log("ERROR", "camera", f"Failed to start camera: {str(e)}")
            return {"success": False, "message": str(e)}

    async def stop_camera(self) -> dict:
        """Stop the camera stream."""
        try:
            if self.mini and hasattr(self.mini, 'media') and self.mini.media:
                if hasattr(self.mini.media, 'stop_camera'):
                    self.mini.media.stop_camera()
                self._camera_started = False
                await self._log("INFO", "camera", "Camera stream stopped")
            return {"success": True, "message": "Camera stopped"}
        except Exception as e:
            await self._log("ERROR", "camera", f"Failed to stop camera: {str(e)}")
            return {"success": False, "message": str(e)}

    async def get_camera_frame(self) -> Optional[np.ndarray]:
        """Get a frame from the robot's camera."""
        try:
            if self.mini and hasattr(self.mini, 'media'):
                # Ensure camera is started
                if not self._camera_started:
                    await self.start_camera()
                return self.mini.media.get_frame()
            return None
        except Exception as e:
            await self._log("ERROR", "camera", f"Failed to get camera frame: {str(e)}")
            return None

    async def capture_image(self) -> dict:
        """Capture an image from the robot's camera and return as base64."""
        import base64
        import io

        # First try WebRTC camera if available
        if self.mini and hasattr(self.mini, 'media') and self.mini.media:
            try:
                # Ensure camera is started
                if not self._camera_started:
                    await self.start_camera()
                    # Give camera time to initialize
                    await asyncio.sleep(0.5)

                # Debug: Log available media methods
                media = self.mini.media
                media_methods = [m for m in dir(media) if not m.startswith('_')]
                await self._log("DEBUG", "camera", f"Media methods: {media_methods}")

                frame = media.get_frame()
                await self._log("DEBUG", "camera", f"Frame result: {type(frame)}, is None: {frame is None}")

                if frame is not None:
                    from PIL import Image
                    if len(frame.shape) == 3 and frame.shape[2] == 3:
                        import cv2
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG', quality=85)
                    img_bytes = buffer.getvalue()
                    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
                    await self._log("INFO", "camera", "Captured image from WebRTC camera")
                    return {
                        "success": True,
                        "image_base64": img_b64,
                        "format": "jpeg",
                        "message": "Image captured via WebRTC"
                    }
                else:
                    await self._log("WARN", "camera", "WebRTC get_frame() returned None")
            except Exception as e:
                import traceback
                await self._log("WARN", "camera", f"WebRTC camera failed: {e}\n{traceback.format_exc()}")

        # Fallback to SSH-based capture
        await self._log("INFO", "camera", "Trying SSH camera capture...")
        return await self._capture_image_via_ssh()

    async def _capture_image_via_ssh(self) -> dict:
        """Capture an image from robot camera via SSH."""
        import base64
        import subprocess
        import tempfile

        ROBOT_USER = "pollen"
        ROBOT_PASSWORD = "root"

        try:
            # Capture image on robot using GStreamer with camera socket
            capture_cmd = (
                f"sshpass -p '{ROBOT_PASSWORD}' ssh -o StrictHostKeyChecking=no "
                f"-o ConnectTimeout=5 {ROBOT_USER}@{self.robot_host} "
                f"\"gst-launch-1.0 unixfdsrc socket-path=/tmp/reachymini_camera_socket num-buffers=1 "
                f"! queue ! videoconvert ! jpegenc quality=85 ! filesink location=/tmp/camera_capture.jpg\" 2>/dev/null"
            )

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: subprocess.run(
                capture_cmd, shell=True, timeout=10, capture_output=True
            ))

            # Copy the image back
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                local_path = tmp.name

            scp_cmd = (
                f"sshpass -p '{ROBOT_PASSWORD}' scp -o StrictHostKeyChecking=no "
                f"-o ConnectTimeout=5 {ROBOT_USER}@{self.robot_host}:/tmp/camera_capture.jpg {local_path}"
            )

            result = await loop.run_in_executor(None, lambda: subprocess.run(
                scp_cmd, shell=True, timeout=10, capture_output=True
            ))

            if result.returncode != 0:
                return {"success": False, "message": "Failed to retrieve image from robot"}

            # Read and encode the image
            with open(local_path, 'rb') as f:
                img_bytes = f.read()

            # Cleanup
            os.unlink(local_path)

            if len(img_bytes) < 1000:
                return {"success": False, "message": "Image capture returned empty data"}

            img_b64 = base64.b64encode(img_bytes).decode('utf-8')
            await self._log("INFO", "camera", f"Captured image via SSH ({len(img_bytes)} bytes)")

            return {
                "success": True,
                "image_base64": img_b64,
                "format": "jpeg",
                "message": "Image captured via SSH"
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "message": "SSH camera capture timed out"}
        except Exception as e:
            await self._log("ERROR", "camera", f"SSH camera capture failed: {str(e)}")
            return {"success": False, "message": f"SSH camera capture failed: {str(e)}"}
    # ==================== TTS METHODS ====================

    async def play_sound_file(self, file_path: str) -> dict:
        """Play an audio file through the robot's speakers."""
        try:
            if self.mini and hasattr(self.mini, 'media'):
                self.mini.media.play_sound(file_path)
                await self._log("INFO", "audio", f"Playing sound file: {file_path}")
                return {"success": True, "message": "Sound played"}
            else:
                await self._log("WARN", "audio", "Audio not available, simulating playback")
                return {"success": True, "message": "Simulated sound playback"}
        except Exception as e:
            await self._log("ERROR", "audio", f"Failed to play sound: {str(e)}")
            return {"success": False, "message": str(e)}

    # ==================== ACTION EXECUTION ====================

    async def execute_action(self, action: str) -> dict:
        """Execute a robot action based on text description."""
        action_lower = action.lower()

        # Camera actions
        if "take picture" in action_lower or "take photo" in action_lower or "capture" in action_lower:
            return await self.capture_image()

        # Antenna actions
        elif "wiggle" in action_lower and "antenna" in action_lower:
            happy = "happy" in action_lower or "excit" in action_lower
            return await self.wiggle_antennas(times=4 if happy else 3)
        elif "raise" in action_lower and "antenna" in action_lower:
            return await self.move_antennas(45, 45, duration=0.5)
        elif "lower" in action_lower and "antenna" in action_lower:
            return await self.move_antennas(-30, -30, duration=0.5)

        # Head actions
        elif "nod" in action_lower:
            return await self.nod()
        elif "shake" in action_lower and "head" in action_lower:
            return await self.shake_head()
        elif "tilt" in action_lower and "head" in action_lower:
            right = "right" in action_lower
            return await self.tilt_head(roll=-15 if right else 15)
        elif "look" in action_lower:
            if "user" in action_lower or "towards" in action_lower or "at me" in action_lower:
                return await self.look_at_user()
            elif "up" in action_lower:
                return await self.move_head(z=30, duration=0.8)
            elif "down" in action_lower:
                return await self.move_head(z=-30, duration=0.8)
            elif "left" in action_lower:
                return await self.move_head(x=-30, duration=0.8)
            elif "right" in action_lower:
                return await self.move_head(x=30, duration=0.8)

        # Body actions
        elif "rotate" in action_lower or "turn" in action_lower:
            if "left" in action_lower:
                return await self.rotate_body(-30, duration=1.0)
            elif "right" in action_lower:
                return await self.rotate_body(30, duration=1.0)

        # Emotion expressions
        elif any(emotion in action_lower for emotion in ["happy", "excited", "joy", "curious",
                                                          "sad", "surprised", "confused"]):
            for emotion in ["happy", "excited", "joy", "curious", "sad", "surprised", "confused"]:
                if emotion in action_lower:
                    return await self.express_emotion(emotion)

        # Default
        else:
            await self._log("WARN", "movement", f"Unknown action: {action}")
            return {"success": False, "message": f"Unknown action: {action}"}

    async def execute_actions(self, actions: List[str]) -> List[dict]:
        """Execute multiple robot actions sequentially."""
        results = []
        for action in actions:
            result = await self.execute_action(action)
            results.append({"action": action, **result})
        return results


robot_service = RobotService()
