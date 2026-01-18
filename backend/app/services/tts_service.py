import asyncio
import httpx
import re
import os
import tempfile
from typing import Optional
from ..config import get_settings

settings = get_settings()

ROBOT_HOST = "192.168.1.33"
ROBOT_USER = "pollen"
ROBOT_PASSWORD = "root"


class TTSService:
    def __init__(self):
        self.api_key = settings.deepgram_api_key
        self.enabled = settings.robot_voice_enabled and bool(self.api_key)
        self.voice = "aura-asteria-en"  # Warm, friendly voice
        self._robot_service = None
        self._ssh_client = None

    def is_configured(self) -> bool:
        return self.enabled

    def _get_robot_service(self):
        """Lazy load robot service to avoid circular imports."""
        if self._robot_service is None:
            from .robot_service import robot_service
            self._robot_service = robot_service
        return self._robot_service

    def _get_ssh_client(self):
        """Get or create SSH client for robot connection."""
        if self._ssh_client is None:
            try:
                import paramiko
                self._ssh_client = paramiko.SSHClient()
                self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self._ssh_client.connect(
                    ROBOT_HOST,
                    username=ROBOT_USER,
                    password=ROBOT_PASSWORD,
                    timeout=5
                )
            except Exception as e:
                print(f"[TTS] SSH connection failed: {e}")
                self._ssh_client = None
        return self._ssh_client

    def clean_text_for_speech(self, text: str) -> str:
        """Remove action brackets and clean text for TTS."""
        text = re.sub(r'\s*\[[^\]]+\]\s*', ' ', text)
        text = re.sub(r'\*[^*]+\*', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    async def speak(self, text: str) -> dict:
        """Convert text to speech and play on robot."""
        if not self.enabled:
            return {"success": False, "message": "TTS not configured"}

        clean_text = self.clean_text_for_speech(text)
        if not clean_text:
            return {"success": False, "message": "No text to speak"}

        try:
            # Generate audio from Deepgram
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.deepgram.com/v1/speak?model={self.voice}",
                    headers={
                        "Authorization": f"Token {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"text": clean_text},
                    timeout=30.0
                )

                if response.status_code != 200:
                    return {"success": False, "message": f"Deepgram error: {response.status_code}"}

                audio_data = response.content

                # Try to play on robot via SSH
                result = await self._play_on_robot(audio_data)
                if result["success"]:
                    return result

                # Fallback: play locally on Mac
                return await self._play_local(audio_data, clean_text)

        except Exception as e:
            return {"success": False, "message": f"TTS error: {str(e)}"}

    async def _play_on_robot(self, audio_data: bytes) -> dict:
        """Play audio on robot via SSH."""
        try:
            import paramiko
            from scp import SCPClient

            # Create temp file
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_file.write(audio_data)
            temp_file.close()
            local_path = temp_file.name
            remote_path = "/tmp/tts_speech.mp3"

            # Connect and transfer
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: ssh.connect(
                ROBOT_HOST,
                username=ROBOT_USER,
                password=ROBOT_PASSWORD,
                timeout=5
            ))

            # SCP the file
            with SCPClient(ssh.get_transport()) as scp:
                await loop.run_in_executor(None, lambda: scp.put(local_path, remote_path))

            # Play the audio on robot using mpv or aplay
            play_cmd = f"mpv --no-video --really-quiet {remote_path} 2>/dev/null || aplay {remote_path} 2>/dev/null || ffplay -nodisp -autoexit {remote_path} 2>/dev/null"
            stdin, stdout, stderr = ssh.exec_command(play_cmd)

            # Don't wait for completion - let it play in background
            ssh.close()

            # Cleanup local temp file
            asyncio.create_task(self._cleanup_file(local_path, delay=2.0))

            return {"success": True, "message": "Playing on robot speakers"}

        except Exception as e:
            print(f"[TTS] Robot playback failed: {e}")
            return {"success": False, "message": str(e)}

    async def _play_local(self, audio_data: bytes, text: str) -> dict:
        """Play audio locally on Mac as fallback."""
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_file.write(audio_data)
            temp_file.close()

            import subprocess
            subprocess.Popen(['afplay', temp_file.name])

            asyncio.create_task(self._cleanup_file(temp_file.name, delay=10.0))

            return {
                "success": True,
                "message": f"Playing locally: {text[:50]}...",
                "audio_size": len(audio_data)
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def _cleanup_file(self, filepath: str, delay: float = 5.0):
        """Clean up temporary file after delay."""
        await asyncio.sleep(delay)
        try:
            os.unlink(filepath)
        except Exception:
            pass


tts_service = TTSService()
