import asyncio
import numpy as np
from datetime import datetime
from typing import Callable, List, Optional, Any
from ..config import get_settings

settings = get_settings()


def create_head_pose(x: float = 0, y: float = 0, z: float = 0, mm: bool = True):
    """Create a head pose target. Wrapper for SDK function."""
    try:
        from reachy_mini import create_head_pose as sdk_create_head_pose
        return sdk_create_head_pose(x=x, y=y, z=z, mm=mm)
    except ImportError:
        return {"x": x, "y": y, "z": z, "mm": mm}


class RobotService:
    def __init__(self):
        self.mini = None
        self.connected = False
        self.connection_mode = settings.robot_connection_mode
        self.log_callbacks: List[Callable] = []
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def connect(self, connection_mode: str = "auto") -> dict:
        """Initialize connection to Reachy Mini robot."""
        try:
            await self._log("INFO", "connection", f"Attempting to connect with mode: {connection_mode}")

            try:
                from reachy_mini import ReachyMini

                if connection_mode == "localhost_only":
                    self.mini = ReachyMini(connection_mode="localhost_only")
                elif connection_mode == "network":
                    self.mini = ReachyMini(connection_mode="network")
                else:
                    self.mini = ReachyMini()

                self.connected = True
                await self._log("INFO", "connection", "Successfully connected to Reachy Mini")

                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

                return {
                    "success": True,
                    "message": "Connected to Reachy Mini",
                    "connection_mode": connection_mode
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
            "last_heartbeat": datetime.utcnow().isoformat() if self.connected else None,
            "robot_info": None,
            "imu_data": None
        }

        if self.connected and self.mini:
            try:
                status["robot_info"] = {
                    "mode": "wireless" if hasattr(self.mini, 'imu') else "lite",
                    "sdk_version": "0.1.0"
                }

                if hasattr(self.mini, 'imu'):
                    imu = self.mini.imu
                    status["imu_data"] = {
                        "accelerometer": imu.accelerometer if hasattr(imu, 'accelerometer') else None,
                        "gyroscope": imu.gyroscope if hasattr(imu, 'gyroscope') else None,
                        "quaternion": imu.quaternion if hasattr(imu, 'quaternion') else None,
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

    async def move_head(self, x: float = 0, y: float = 0, z: float = 0,
                        duration: float = 1.0, method: str = "minjerk") -> dict:
        """Move the robot's head to a target position."""
        try:
            await self._log("INFO", "movement", f"Moving head to ({x}, {y}, {z})")

            if self.mini:
                head_pose = create_head_pose(x=x, y=y, z=z, mm=True)
                self.mini.goto_target(head=head_pose, duration=duration, method=method)
                await asyncio.sleep(duration)
                return {"success": True, "message": f"Head moved to ({x}, {y}, {z})"}
            else:
                await self._log("INFO", "movement", "Simulating head movement")
                await asyncio.sleep(duration)
                return {"success": True, "message": f"Simulated head move to ({x}, {y}, {z})"}

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

    async def execute_action(self, action: str) -> dict:
        """Execute a robot action based on text description."""
        action_lower = action.lower()

        if "wiggle" in action_lower and "antenna" in action_lower:
            return await self.wiggle_antennas()
        elif "nod" in action_lower:
            return await self.nod()
        elif "shake" in action_lower and "head" in action_lower:
            return await self.shake_head()
        elif "look" in action_lower and ("user" in action_lower or "towards" in action_lower):
            return await self.look_at_user()
        elif "raise" in action_lower and "antenna" in action_lower:
            return await self.move_antennas(45, 45, duration=0.5)
        elif "lower" in action_lower and "antenna" in action_lower:
            return await self.move_antennas(-30, -30, duration=0.5)
        elif "look" in action_lower and "up" in action_lower:
            return await self.move_head(z=30, duration=0.8)
        elif "look" in action_lower and "down" in action_lower:
            return await self.move_head(z=-30, duration=0.8)
        elif "look" in action_lower and "left" in action_lower:
            return await self.move_head(x=-30, duration=0.8)
        elif "look" in action_lower and "right" in action_lower:
            return await self.move_head(x=30, duration=0.8)
        elif "rotate" in action_lower or "turn" in action_lower:
            if "left" in action_lower:
                return await self.rotate_body(-30, duration=1.0)
            elif "right" in action_lower:
                return await self.rotate_body(30, duration=1.0)
        else:
            await self._log("WARN", "movement", f"Unknown action: {action}")
            return {"success": False, "message": f"Unknown action: {action}"}


robot_service = RobotService()
