import asyncio
from datetime import datetime
from typing import Callable, List, Optional, Any
from ..config import get_settings

settings = get_settings()


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


robot_service = RobotService()
