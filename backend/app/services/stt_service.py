"""
Speech-to-Text Service using Deepgram streaming API v5.
Handles real-time audio transcription from the robot's microphone.
"""
import asyncio
from typing import Callable, Optional, List
from ..config import get_settings

settings = get_settings()


class STTService:
    """Deepgram streaming STT service for real-time transcription."""

    def __init__(self):
        self.api_key = settings.deepgram_api_key
        self.enabled = bool(self.api_key)
        self._connection = None
        self._is_listening = False
        self._transcript_callbacks: List[Callable] = []
        self._error_callbacks: List[Callable] = []
        self._client = None
        self._loop = None

    def is_configured(self) -> bool:
        """Check if STT is properly configured."""
        return self.enabled

    def is_listening(self) -> bool:
        """Check if currently listening for audio."""
        return self._is_listening

    def add_transcript_callback(self, callback: Callable):
        """Register a callback for transcript events."""
        self._transcript_callbacks.append(callback)

    def remove_transcript_callback(self, callback: Callable):
        """Remove a transcript callback."""
        if callback in self._transcript_callbacks:
            self._transcript_callbacks.remove(callback)

    def add_error_callback(self, callback: Callable):
        """Register a callback for error events."""
        self._error_callbacks.append(callback)

    def remove_error_callback(self, callback: Callable):
        """Remove an error callback."""
        if callback in self._error_callbacks:
            self._error_callbacks.remove(callback)

    async def _notify_transcript(self, transcript: str, is_final: bool):
        """Notify all callbacks of a transcript event."""
        for callback in self._transcript_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(transcript, is_final)
                else:
                    callback(transcript, is_final)
            except Exception as e:
                print(f"[STT] Callback error: {e}")

    async def _notify_error(self, error: str):
        """Notify all callbacks of an error."""
        for callback in self._error_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(error)
                else:
                    callback(error)
            except Exception as e:
                print(f"[STT] Error callback failed: {e}")

    def _schedule_callback(self, coro):
        """Schedule an async callback on the main event loop."""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, self._loop)

    async def start_listening(self) -> dict:
        """Start the Deepgram streaming connection."""
        if not self.enabled:
            return {"success": False, "message": "STT not configured - missing API key"}

        if self._is_listening:
            return {"success": True, "message": "Already listening"}

        try:
            # Import deepgram SDK v5
            from deepgram import DeepgramClient
            from deepgram.core.events import EventType

            # Store the event loop for callbacks
            self._loop = asyncio.get_event_loop()

            self._client = DeepgramClient(api_key=self.api_key)

            # Use v1 API with LiveOptions-style parameters
            self._connection_manager = self._client.listen.v1.connect(
                model="nova-2",
                language="en-US",
                smart_format=True,
                interim_results=True,
                utterance_end_ms=1000,
                vad_events=True,
                encoding="linear16",
                sample_rate=16000,
                channels=1
            )

            # Enter the context manager
            self._connection = self._connection_manager.__enter__()

            # Set up event handlers
            def on_message(message):
                try:
                    if hasattr(message, "channel"):
                        transcript = message.channel.alternatives[0].transcript
                        if transcript:
                            is_final = getattr(message, "is_final", True)
                            self._schedule_callback(self._notify_transcript(transcript, is_final))
                except Exception as e:
                    print(f"[STT] Message handler error: {e}")

            def on_error(error):
                print(f"[STT] Error: {error}")
                self._schedule_callback(self._notify_error(str(error)))

            def on_close(_):
                print("[STT] Connection closed")
                self._is_listening = False

            self._connection.on(EventType.MESSAGE, on_message)
            self._connection.on(EventType.ERROR, on_error)
            self._connection.on(EventType.CLOSE, on_close)

            # Start listening
            self._connection.start_listening()

            self._is_listening = True
            print("[STT] Deepgram connection started")
            return {"success": True, "message": "STT listening started"}

        except ImportError as e:
            print(f"[STT] Import error: {e}")
            return {"success": False, "message": "deepgram-sdk not installed"}
        except Exception as e:
            print(f"[STT] Start error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"STT start failed: {str(e)}"}

    async def stop_listening(self) -> dict:
        """Stop the Deepgram streaming connection."""
        if not self._is_listening:
            return {"success": True, "message": "Not listening"}

        try:
            if self._connection:
                try:
                    self._connection.finish()
                except Exception:
                    pass

            if hasattr(self, '_connection_manager') and self._connection_manager:
                try:
                    self._connection_manager.__exit__(None, None, None)
                except Exception:
                    pass
                self._connection_manager = None

            self._connection = None
            self._is_listening = False
            print("[STT] Stopped listening")
            return {"success": True, "message": "STT stopped"}

        except Exception as e:
            print(f"[STT] Stop error: {e}")
            return {"success": False, "message": f"STT stop failed: {str(e)}"}

    async def send_audio(self, audio_data: bytes) -> bool:
        """Send audio data to Deepgram for transcription.

        Args:
            audio_data: Raw PCM audio bytes (16-bit, 16kHz, mono)

        Returns:
            True if audio was sent successfully
        """
        if not self._is_listening or not self._connection:
            return False

        try:
            self._connection.send_media(audio_data)
            return True
        except Exception as e:
            print(f"[STT] Send audio error: {e}")
            return False

    async def get_status(self) -> dict:
        """Get current STT service status."""
        return {
            "configured": self.enabled,
            "listening": self._is_listening,
            "callback_count": len(self._transcript_callbacks)
        }


# Singleton instance
stt_service = STTService()
