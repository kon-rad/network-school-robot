import asyncio
import os
import tempfile
import re
from typing import Optional
from elevenlabs import ElevenLabs
from ..config import get_settings

settings = get_settings()

ROBOT_USER = "pollen"
ROBOT_PASSWORD = "root"


class TTSService:
    def __init__(self):
        self.api_key = settings.elevenlabs_api_key
        self.enabled = settings.robot_voice_enabled and bool(self.api_key)
        self.voice_id = "JBFqnCBsd6RMkjVDRZzb"  # George - warm, friendly voice
        self.model_id = "eleven_multilingual_v2"
        self._robot_service = None
        self._client = None

    def is_configured(self) -> bool:
        return self.enabled

    def _get_client(self):
        """Lazy load ElevenLabs client."""
        if self._client is None and self.api_key:
            self._client = ElevenLabs(api_key=self.api_key)
        return self._client

    def _get_robot_service(self):
        """Lazy load robot service to avoid circular imports."""
        if self._robot_service is None:
            from .robot_service import robot_service
            self._robot_service = robot_service
        return self._robot_service

    def _get_robot_host(self):
        """Get robot host from settings."""
        return settings.robot_host or "reachy-mini.local"

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
            client = self._get_client()
            if not client:
                return {"success": False, "message": "ElevenLabs client not initialized"}

            # Generate audio from ElevenLabs
            loop = asyncio.get_event_loop()
            audio_generator = await loop.run_in_executor(
                None,
                lambda: client.text_to_speech.convert(
                    voice_id=self.voice_id,
                    text=clean_text,
                    model_id=self.model_id,
                    output_format="mp3_44100_128"
                )
            )

            # Collect audio bytes from generator
            audio_data = b"".join(chunk for chunk in audio_generator)

            # Try to play on robot via SSH
            result = await self._play_on_robot(audio_data)
            if result["success"]:
                return result

            # Fallback: play locally on Mac
            return await self._play_local(audio_data, clean_text)

        except Exception as e:
            print(f"[TTS] Error: {e}")
            return {"success": False, "message": f"TTS error: {str(e)}"}

    async def _play_on_robot(self, audio_data: bytes) -> dict:
        """Play audio on robot via Reachy SDK."""
        try:
            import paramiko
            from scp import SCPClient

            # Transfer file to robot first
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_file.write(audio_data)
            temp_file.close()
            local_path = temp_file.name
            remote_path = "/tmp/tts_speech.mp3"

            # Connect and transfer
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            robot_host = self._get_robot_host()
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: ssh.connect(
                robot_host,
                username=ROBOT_USER,
                password=ROBOT_PASSWORD,
                timeout=5
            ))

            # SCP the file
            with SCPClient(ssh.get_transport()) as scp:
                await loop.run_in_executor(None, lambda: scp.put(local_path, remote_path))

            ssh.close()

            # Cleanup local temp file
            asyncio.create_task(self._cleanup_file(local_path, delay=2.0))

            # Use Reachy SDK to play (same process has audio device)
            robot = self._get_robot_service()
            if robot.mini and hasattr(robot.mini, 'media'):
                print(f"[TTS] Playing via Reachy SDK: {remote_path}")
                await loop.run_in_executor(None, lambda: robot.mini.media.play_sound(remote_path))
                return {"success": True, "message": "Playing on robot speakers via SDK"}
            else:
                print("[TTS] Reachy SDK not available, trying SSH playback")
                # Fallback to SSH-based playback
                return await self._play_via_ssh(remote_path)

        except Exception as e:
            print(f"[TTS] Robot playback failed: {e}")
            return {"success": False, "message": str(e)}

    async def _play_via_ssh(self, remote_path: str) -> dict:
        """Fallback: Play audio via SSH command."""
        try:
            import paramiko

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            robot_host = self._get_robot_host()
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: ssh.connect(
                robot_host,
                username=ROBOT_USER,
                password=ROBOT_PASSWORD,
                timeout=5
            ))

            play_cmd = f"gst-play-1.0 {remote_path} 2>&1"
            stdin, stdout, stderr = ssh.exec_command(play_cmd)
            exit_status = stdout.channel.recv_exit_status()
            ssh.close()

            return {"success": True, "message": "Playing via SSH"}
        except Exception as e:
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
