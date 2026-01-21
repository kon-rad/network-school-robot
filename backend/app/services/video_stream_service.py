"""Video streaming service for high FPS camera streaming via WebSocket."""

import asyncio
import base64
import io
import time
from typing import Callable, Optional, Set
from dataclasses import dataclass

import numpy as np


@dataclass
class StreamConfig:
    """Video stream configuration."""
    target_fps: int = 60
    quality: int = 60
    max_width: int = 640
    max_height: int = 480


class VideoStreamService:
    """Service for streaming video from robot camera at high FPS."""

    def __init__(self):
        self._subscribers: Set[Callable] = set()
        self._is_streaming = False
        self._stream_task: Optional[asyncio.Task] = None
        self._config = StreamConfig()
        self._frame_count = 0
        self._last_fps_time = time.time()
        self._actual_fps = 0.0

    def configure(self, target_fps: int = 30, quality: int = 70,
                  max_width: int = 640, max_height: int = 480):
        """Configure stream parameters."""
        self._config = StreamConfig(
            target_fps=target_fps,
            quality=quality,
            max_width=max_width,
            max_height=max_height
        )

    @property
    def is_streaming(self) -> bool:
        return self._is_streaming

    @property
    def actual_fps(self) -> float:
        return self._actual_fps

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)

    def subscribe(self, callback: Callable):
        """Subscribe to video frames."""
        self._subscribers.add(callback)

    def unsubscribe(self, callback: Callable):
        """Unsubscribe from video frames."""
        self._subscribers.discard(callback)

    async def start_streaming(self):
        """Start the video streaming loop."""
        if self._is_streaming:
            return

        self._is_streaming = True
        self._frame_count = 0
        self._last_fps_time = time.time()
        self._stream_task = asyncio.create_task(self._stream_loop())

    async def stop_streaming(self):
        """Stop the video streaming loop."""
        self._is_streaming = False
        if self._stream_task:
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass
            self._stream_task = None

    async def _stream_loop(self):
        """Main streaming loop that captures and broadcasts frames."""
        from .robot_service import robot_service

        frame_interval = 1.0 / self._config.target_fps
        consecutive_failures = 0
        max_failures = 10

        # Ensure camera is started
        if robot_service.connected and robot_service.mini and hasattr(robot_service.mini, 'media'):
            if not robot_service._camera_started:
                print("Starting camera for video stream...")
                await robot_service.start_camera()
                await asyncio.sleep(0.5)
        else:
            print("Robot not connected or no media available for video stream")

        while self._is_streaming:
            loop_start = time.time()

            try:
                if not self._subscribers:
                    # No subscribers, slow down
                    await asyncio.sleep(0.1)
                    continue

                # Capture frame
                frame_data = await self._capture_frame(robot_service)

                if frame_data:
                    consecutive_failures = 0
                    # Broadcast to all subscribers
                    await self._broadcast_frame(frame_data)

                    # Update FPS counter
                    self._frame_count += 1
                    now = time.time()
                    elapsed = now - self._last_fps_time
                    if elapsed >= 1.0:
                        self._actual_fps = self._frame_count / elapsed
                        self._frame_count = 0
                        self._last_fps_time = now
                else:
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        # Send error message to subscribers
                        await self._broadcast_frame({
                            "error": "No frames available from camera",
                            "fps": 0
                        })
                        consecutive_failures = 0
                        await asyncio.sleep(1.0)
                        continue

            except Exception as e:
                print(f"Stream loop error: {e}")
                consecutive_failures += 1

            # Maintain target FPS
            elapsed = time.time() - loop_start
            sleep_time = max(0, frame_interval - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

    async def _capture_frame(self, robot_service) -> Optional[dict]:
        """Capture and encode a single frame."""
        try:
            frame = None

            # Try WebRTC camera first
            if robot_service.mini and hasattr(robot_service.mini, 'media'):
                media = robot_service.mini.media
                if media:
                    frame = media.get_frame()

            if frame is None:
                return None

            # Resize if needed
            frame = self._resize_frame(frame)

            # Encode to JPEG
            img_b64 = self._encode_frame(frame)

            return {
                "image_base64": img_b64,
                "format": "jpeg",
                "width": frame.shape[1],
                "height": frame.shape[0],
                "fps": round(self._actual_fps, 1)
            }

        except Exception as e:
            print(f"Frame capture error: {e}")
            return None

    def _resize_frame(self, frame: np.ndarray) -> np.ndarray:
        """Resize frame if it exceeds max dimensions."""
        import cv2

        h, w = frame.shape[:2]
        max_w, max_h = self._config.max_width, self._config.max_height

        if w <= max_w and h <= max_h:
            return frame

        # Calculate scale
        scale = min(max_w / w, max_h / h)
        new_w, new_h = int(w * scale), int(h * scale)

        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    def _encode_frame(self, frame: np.ndarray) -> str:
        """Encode frame to base64 JPEG."""
        import cv2

        # Convert BGR to RGB if needed
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Encode to JPEG
        from PIL import Image
        img = Image.fromarray(frame)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=self._config.quality)
        img_bytes = buffer.getvalue()

        return base64.b64encode(img_bytes).decode('utf-8')

    async def _broadcast_frame(self, frame_data: dict):
        """Broadcast frame to all subscribers."""
        dead_subscribers = []

        for callback in self._subscribers.copy():
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(frame_data)
                else:
                    callback(frame_data)
            except Exception as e:
                print(f"Subscriber callback error: {e}")
                dead_subscribers.append(callback)

        # Remove dead subscribers
        for sub in dead_subscribers:
            self._subscribers.discard(sub)

    def get_status(self) -> dict:
        """Get current streaming status."""
        return {
            "streaming": self._is_streaming,
            "subscribers": len(self._subscribers),
            "actual_fps": round(self._actual_fps, 1),
            "target_fps": self._config.target_fps,
            "quality": self._config.quality,
            "resolution": f"{self._config.max_width}x{self._config.max_height}"
        }


# Singleton instance
video_stream_service = VideoStreamService()
