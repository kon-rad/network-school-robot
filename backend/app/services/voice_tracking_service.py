import asyncio
import math
from typing import Optional, Callable
from ..config import get_settings

settings = get_settings()


class VoiceTrackingService:
    """
    Service for tracking voice direction and moving the robot's head
    to face the speaker, like natural human interaction.
    """

    def __init__(self):
        self._robot_service = None
        self._tracking_enabled = False
        self._tracking_task: Optional[asyncio.Task] = None
        self._last_doa: Optional[float] = None
        self._smoothing_factor = 0.4  # Smoothing for natural head movement
        self._min_movement_threshold = 3.0  # Degrees to trigger movement (lowered for responsiveness)
        self._tracking_interval = 0.05  # Check voice direction 20 times per second
        self._callbacks: list[Callable] = []
        self._continuous_mode = True  # Track continuously, not just on speech detection

    def _get_robot_service(self):
        """Lazy load robot service to avoid circular imports."""
        if self._robot_service is None:
            from .robot_service import robot_service
            self._robot_service = robot_service
        return self._robot_service

    def add_callback(self, callback: Callable):
        """Add callback for voice detection events."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable):
        """Remove callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def _notify_callbacks(self, event: dict):
        """Notify all callbacks of voice detection event."""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception:
                pass

    def doa_to_head_angle(self, doa: float) -> float:
        """
        Convert Direction of Arrival (DoA) to head yaw angle.

        DoA typically ranges from -180 to 180 degrees:
        - 0 = directly in front
        - negative = left side
        - positive = right side

        We map this to head rotation where:
        - 0 = looking straight
        - negative = looking left
        - positive = looking right
        """
        # Clamp DoA to reasonable range for head movement
        # Robot head typically can rotate about -40 to +40 degrees
        max_head_angle = 35.0

        # Scale DoA to head angle range
        # If sound is at 90 degrees to the side, we want max head turn
        scale_factor = max_head_angle / 90.0
        head_angle = doa * scale_factor

        # Clamp to safe range
        head_angle = max(-max_head_angle, min(max_head_angle, head_angle))

        return head_angle

    async def look_at_speaker(self, doa: float, smooth: bool = True) -> dict:
        """
        Turn the robot's head towards the detected voice direction.

        Args:
            doa: Direction of arrival in degrees
            smooth: Whether to apply smoothing for natural movement
        """
        robot = self._get_robot_service()

        if not robot.connected:
            return {"success": False, "message": "Robot not connected"}

        # Apply smoothing if we have a previous direction
        if smooth and self._last_doa is not None:
            doa = self._last_doa + self._smoothing_factor * (doa - self._last_doa)

        self._last_doa = doa

        # Convert DoA to head angle
        head_angle = self.doa_to_head_angle(doa)

        # Move head to face speaker
        # x controls left/right rotation
        result = await robot.move_head(
            x=head_angle,
            y=0,
            z=0,
            duration=0.3,  # Quick but smooth movement
            method="minjerk"
        )

        return {
            "success": result.get("success", False),
            "message": f"Looking towards speaker at {doa:.1f}° (head: {head_angle:.1f}°)",
            "doa": doa,
            "head_angle": head_angle
        }

    async def _tracking_loop(self):
        """Main tracking loop that continuously monitors voice direction."""
        robot = self._get_robot_service()
        consecutive_detections = 0

        while self._tracking_enabled:
            try:
                # Get current voice direction from robot's DoA sensor
                voice_info = await robot.get_voice_direction()

                if voice_info:
                    doa = voice_info.get("direction_of_arrival")
                    speech_detected = voice_info.get("speech_detected", False)

                    if doa is not None:
                        # In continuous mode, always track the direction
                        # In speech mode, only track when speech is detected
                        should_track = self._continuous_mode or speech_detected

                        if should_track:
                            # Convert radians to degrees if needed (DoA from API is in radians)
                            doa_degrees = math.degrees(doa) if abs(doa) < 10 else doa

                            # Check if movement is significant enough
                            if self._last_doa is None or abs(doa_degrees - self._last_doa) > self._min_movement_threshold:
                                await self.look_at_speaker(doa_degrees)

                                if speech_detected:
                                    consecutive_detections += 1
                                    await self._notify_callbacks({
                                        "event": "speech_detected",
                                        "doa": doa_degrees,
                                        "head_angle": self.doa_to_head_angle(doa_degrees),
                                        "consecutive": consecutive_detections
                                    })
                        else:
                            consecutive_detections = 0

                await asyncio.sleep(self._tracking_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(self._tracking_interval)

    async def start_tracking(self) -> dict:
        """Start voice tracking - robot will follow speaker's voice."""
        if self._tracking_enabled:
            return {"success": True, "message": "Tracking already active"}

        robot = self._get_robot_service()

        if not robot.connected:
            return {"success": False, "message": "Robot not connected"}

        # Start audio recording for voice detection
        await robot.start_recording()

        self._tracking_enabled = True
        self._tracking_task = asyncio.create_task(self._tracking_loop())

        return {"success": True, "message": "Voice tracking started - robot will follow speaker"}

    async def stop_tracking(self) -> dict:
        """Stop voice tracking."""
        if not self._tracking_enabled:
            return {"success": True, "message": "Tracking already stopped"}

        self._tracking_enabled = False

        if self._tracking_task:
            self._tracking_task.cancel()
            try:
                await self._tracking_task
            except asyncio.CancelledError:
                pass
            self._tracking_task = None

        robot = self._get_robot_service()
        await robot.stop_recording()

        # Return head to center
        await robot.look_at_user()

        self._last_doa = None

        return {"success": True, "message": "Voice tracking stopped"}

    def is_tracking(self) -> bool:
        """Check if voice tracking is currently active."""
        return self._tracking_enabled

    async def get_status(self) -> dict:
        """Get current tracking status."""
        return {
            "tracking_enabled": self._tracking_enabled,
            "last_doa": self._last_doa,
            "smoothing_factor": self._smoothing_factor,
            "min_movement_threshold": self._min_movement_threshold
        }

    def set_smoothing(self, factor: float):
        """Set smoothing factor (0.0 = no smoothing, 1.0 = instant)."""
        self._smoothing_factor = max(0.0, min(1.0, factor))

    def set_movement_threshold(self, degrees: float):
        """Set minimum movement threshold in degrees."""
        self._min_movement_threshold = max(1.0, degrees)


# Singleton instance
voice_tracking_service = VoiceTrackingService()
