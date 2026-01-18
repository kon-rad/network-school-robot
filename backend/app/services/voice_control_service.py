"""
Voice Control Orchestrator Service.
Main service that coordinates STT, command parsing, Claude Code execution,
TTS response, and robot feedback.
"""
import asyncio
import numpy as np
from typing import Callable, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class VoiceControlState(Enum):
    """Overall voice control system state."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class VoiceControlEvent:
    """Event from voice control system."""
    type: str  # "transcript", "command", "response", "status", "error"
    data: dict
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class VoiceControlService:
    """Main orchestrator for voice-controlled Claude Code interaction."""

    AUDIO_SAMPLE_RATE = 16000  # Hz
    AUDIO_CHUNK_DURATION = 0.05  # 50ms chunks (20 Hz)
    AUDIO_CHUNK_SIZE = int(AUDIO_SAMPLE_RATE * AUDIO_CHUNK_DURATION)

    def __init__(self):
        self._state = VoiceControlState.STOPPED
        self._audio_task: Optional[asyncio.Task] = None
        self._event_callbacks: List[Callable] = []
        self._last_command: Optional[str] = None
        self._last_response: Optional[str] = None

        # Lazy-loaded service references
        self._stt_service = None
        self._command_parser = None
        self._claude_code = None
        self._tts_service = None
        self._robot_service = None
        self._chat_service = None

    @property
    def state(self) -> VoiceControlState:
        """Current system state."""
        return self._state

    def is_running(self) -> bool:
        """Check if voice control is active."""
        return self._state not in [VoiceControlState.STOPPED, VoiceControlState.ERROR]

    # ==================== Service Accessors ====================

    def _get_stt_service(self):
        """Lazy load STT service."""
        if self._stt_service is None:
            from .stt_service import stt_service
            self._stt_service = stt_service
        return self._stt_service

    def _get_command_parser(self):
        """Lazy load command parser."""
        if self._command_parser is None:
            from .command_parser_service import command_parser_service
            self._command_parser = command_parser_service
        return self._command_parser

    def _get_claude_code(self):
        """Lazy load Claude Code service."""
        if self._claude_code is None:
            from .claude_code_service import claude_code_service
            self._claude_code = claude_code_service
        return self._claude_code

    def _get_tts_service(self):
        """Lazy load TTS service."""
        if self._tts_service is None:
            from .tts_service import tts_service
            self._tts_service = tts_service
        return self._tts_service

    def _get_robot_service(self):
        """Lazy load robot service."""
        if self._robot_service is None:
            from .robot_service import robot_service
            self._robot_service = robot_service
        return self._robot_service

    def _get_chat_service(self):
        """Lazy load chat service for non-Claude-Code commands."""
        if self._chat_service is None:
            try:
                from .chat_service import chat_service
                self._chat_service = chat_service
            except ImportError:
                self._chat_service = None
        return self._chat_service

    # ==================== Event System ====================

    def add_event_callback(self, callback: Callable):
        """Register callback for voice control events."""
        self._event_callbacks.append(callback)

    def remove_event_callback(self, callback: Callable):
        """Remove an event callback."""
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)

    async def _emit_event(self, event_type: str, data: dict):
        """Emit an event to all callbacks."""
        event = VoiceControlEvent(type=event_type, data=data)
        for callback in self._event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"[VoiceControl] Event callback error: {e}")

    def _set_state(self, state: VoiceControlState):
        """Update state and emit event."""
        if self._state != state:
            old_state = self._state
            self._state = state
            print(f"[VoiceControl] State: {old_state.value} -> {state.value}")
            asyncio.create_task(self._emit_event("status", {
                "state": state.value,
                "previous": old_state.value
            }))

    # ==================== Control Methods ====================

    async def start(self) -> dict:
        """Start voice control system."""
        if self.is_running():
            return {"success": True, "message": "Already running"}

        try:
            self._set_state(VoiceControlState.STARTING)

            # Initialize STT
            stt = self._get_stt_service()
            if not stt.is_configured():
                self._set_state(VoiceControlState.ERROR)
                return {"success": False, "message": "STT not configured - check DEEPGRAM_API_KEY"}

            # Set up transcript callback
            stt.add_transcript_callback(self._on_transcript)

            # Start STT
            result = await stt.start_listening()
            if not result["success"]:
                self._set_state(VoiceControlState.ERROR)
                return result

            # Set up command parser callback
            parser = self._get_command_parser()
            parser.add_command_callback(self._on_command)

            # Start audio capture loop
            self._audio_task = asyncio.create_task(self._audio_loop())

            self._set_state(VoiceControlState.RUNNING)
            await self._emit_event("status", {"message": "Voice control started"})

            return {"success": True, "message": "Voice control started"}

        except Exception as e:
            self._set_state(VoiceControlState.ERROR)
            return {"success": False, "message": f"Start failed: {str(e)}"}

    async def stop(self) -> dict:
        """Stop voice control system."""
        if not self.is_running():
            return {"success": True, "message": "Already stopped"}

        try:
            # Cancel audio loop
            if self._audio_task:
                self._audio_task.cancel()
                try:
                    await self._audio_task
                except asyncio.CancelledError:
                    pass
                self._audio_task = None

            # Stop STT
            stt = self._get_stt_service()
            stt.remove_transcript_callback(self._on_transcript)
            await stt.stop_listening()

            # Reset parser
            parser = self._get_command_parser()
            parser.remove_command_callback(self._on_command)
            parser.reset()

            self._set_state(VoiceControlState.STOPPED)
            await self._emit_event("status", {"message": "Voice control stopped"})

            return {"success": True, "message": "Voice control stopped"}

        except Exception as e:
            self._set_state(VoiceControlState.ERROR)
            return {"success": False, "message": f"Stop failed: {str(e)}"}

    async def execute_manual_command(self, command: str, use_claude_code: bool = True) -> dict:
        """Execute a command manually (for testing)."""
        if use_claude_code:
            return await self._execute_claude_code_command(command)
        else:
            return await self._execute_chat_command(command)

    # ==================== Audio Processing ====================

    async def _audio_loop(self):
        """Main loop for capturing and processing audio from robot."""
        robot = self._get_robot_service()
        stt = self._get_stt_service()

        # Start recording on robot
        await robot.start_recording()

        try:
            while self._state in [VoiceControlState.RUNNING, VoiceControlState.STARTING]:
                try:
                    # Get audio sample from robot
                    audio = await robot.get_audio_sample()

                    if audio is not None and len(audio) > 0:
                        # Convert to bytes (16-bit PCM)
                        if audio.dtype != np.int16:
                            # Normalize and convert to int16
                            if audio.dtype == np.float32 or audio.dtype == np.float64:
                                audio = (audio * 32767).astype(np.int16)
                            else:
                                audio = audio.astype(np.int16)

                        audio_bytes = audio.tobytes()
                        await stt.send_audio(audio_bytes)

                    # Sleep for chunk duration (20 Hz)
                    await asyncio.sleep(self.AUDIO_CHUNK_DURATION)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"[VoiceControl] Audio loop error: {e}")
                    await asyncio.sleep(0.1)

        finally:
            # Stop recording on robot
            await robot.stop_recording()

    # ==================== Callbacks ====================

    async def _on_transcript(self, transcript: str, is_final: bool):
        """Handle transcript from STT."""
        if not transcript.strip():
            return

        await self._emit_event("transcript", {
            "text": transcript,
            "is_final": is_final
        })

        # Process through command parser
        parser = self._get_command_parser()
        command = parser.process_transcript(transcript, is_final)

        if command:
            # Command detected - trigger execution
            await self._handle_command(command)

    def _on_command(self, command):
        """Synchronous callback for command parser."""
        # This is called synchronously, so we schedule the async handler
        asyncio.create_task(self._handle_command(command))

    async def _handle_command(self, command):
        """Handle a detected command."""
        from .command_parser_service import ParsedCommand

        if not isinstance(command, ParsedCommand):
            return

        await self._emit_event("command", {
            "text": command.command,
            "is_claude_code": command.is_claude_code,
            "confidence": command.confidence
        })

        # Robot feedback - wiggle antennas on wake word
        robot = self._get_robot_service()
        if robot.connected:
            asyncio.create_task(robot.wiggle_antennas(times=2, angle=20))

        self._set_state(VoiceControlState.PROCESSING)
        self._last_command = command.command

        # Execute command
        if command.is_claude_code:
            result = await self._execute_claude_code_command(command.command)
        else:
            result = await self._execute_chat_command(command.command)

        self._last_response = result.get("response", "")

        # Speak response
        if self._last_response:
            await self._speak_response(self._last_response)

        # Return to running state
        parser = self._get_command_parser()
        parser.command_completed()
        self._set_state(VoiceControlState.RUNNING)

    # ==================== Command Execution ====================

    async def _execute_claude_code_command(self, command: str) -> dict:
        """Execute command via Claude Code CLI."""
        claude_code = self._get_claude_code()
        robot = self._get_robot_service()

        # Robot feedback - nod to acknowledge
        if robot.connected:
            asyncio.create_task(robot.nod(times=1))

        await self._emit_event("status", {"message": f"Executing: {command[:50]}..."})

        result = await claude_code.execute_command(command)

        # Parse output for response
        response = self._extract_response(result.output)

        await self._emit_event("response", {
            "command": command,
            "output": result.output,
            "response": response,
            "status": result.status.value
        })

        return {
            "success": result.status.value == "completed",
            "output": result.output,
            "response": response
        }

    async def _execute_chat_command(self, command: str) -> dict:
        """Execute command via chat service (non-code commands)."""
        chat_service = self._get_chat_service()

        if chat_service is None:
            return {
                "success": False,
                "response": "Chat service not available"
            }

        try:
            response = await chat_service.chat(command)
            return {
                "success": True,
                "response": response
            }
        except Exception as e:
            return {
                "success": False,
                "response": f"Error: {str(e)}"
            }

    def _extract_response(self, output: str) -> str:
        """Extract speakable response from Claude Code output."""
        if not output:
            return "Done."

        lines = output.strip().split("\n")

        # Filter out code blocks, file paths, and technical output
        response_lines = []
        in_code_block = False

        for line in lines:
            stripped = line.strip()

            # Skip code blocks
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            # Skip file paths and technical lines
            if stripped.startswith("/") or stripped.startswith("./"):
                continue
            if "created" in stripped.lower() and "/" in stripped:
                continue
            if stripped.startswith("$") or stripped.startswith(">"):
                continue

            # Keep conversational lines
            if stripped and len(stripped) > 5:
                response_lines.append(stripped)

        if response_lines:
            # Return first few meaningful lines
            response = " ".join(response_lines[:3])
            # Truncate if too long
            if len(response) > 200:
                response = response[:197] + "..."
            return response

        return "Done."

    # ==================== TTS ====================

    async def _speak_response(self, text: str):
        """Speak response via TTS."""
        self._set_state(VoiceControlState.SPEAKING)

        tts = self._get_tts_service()
        if tts.is_configured():
            await tts.speak(text)

        await self._emit_event("spoke", {"text": text})

    # ==================== Status ====================

    async def get_status(self) -> dict:
        """Get comprehensive status of voice control system."""
        stt = self._get_stt_service()
        parser = self._get_command_parser()
        claude_code = self._get_claude_code()
        robot = self._get_robot_service()

        return {
            "state": self._state.value,
            "is_running": self.is_running(),
            "last_command": self._last_command,
            "last_response": self._last_response,
            "services": {
                "stt": await stt.get_status(),
                "parser": parser.get_status(),
                "claude_code": claude_code.get_status(),
                "robot_connected": robot.connected
            }
        }


# Singleton instance
voice_control_service = VoiceControlService()
