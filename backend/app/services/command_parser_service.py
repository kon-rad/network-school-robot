"""
Command Parser Service for voice control.
Handles wake word detection and command extraction from transcripts.
"""
import re
from enum import Enum
from typing import Callable, List, Optional, Tuple
from dataclasses import dataclass


class VoiceMode(Enum):
    """Voice control modes."""
    IDLE = "idle"           # Waiting for wake word
    LISTENING = "listening"  # Actively listening for command
    PROCESSING = "processing"  # Processing a command


@dataclass
class ParsedCommand:
    """Represents a parsed voice command."""
    raw_text: str
    command: str
    is_claude_code: bool  # True if directed to Claude Code CLI
    confidence: float


class CommandParserService:
    """Parses voice transcripts for wake words and commands."""

    # Wake words that activate Claude Code mode
    WAKE_WORDS_CLAUDE_CODE = [
        "hey claude",
        "hey claude code",
        "claude code",
        "claude",
    ]

    # Phrases that indicate end of command
    END_PHRASES = [
        "that's it",
        "that's all",
        "end command",
        "done",
        "thank you",
        "thanks",
    ]

    # Timeout in seconds after wake word before returning to idle
    LISTENING_TIMEOUT = 10.0

    def __init__(self):
        self._mode = VoiceMode.IDLE
        self._current_transcript = ""
        self._command_callbacks: List[Callable] = []
        self._mode_callbacks: List[Callable] = []

    @property
    def mode(self) -> VoiceMode:
        """Current voice control mode."""
        return self._mode

    def add_command_callback(self, callback: Callable):
        """Register callback for when a command is detected."""
        self._command_callbacks.append(callback)

    def remove_command_callback(self, callback: Callable):
        """Remove a command callback."""
        if callback in self._command_callbacks:
            self._command_callbacks.remove(callback)

    def add_mode_callback(self, callback: Callable):
        """Register callback for mode changes."""
        self._mode_callbacks.append(callback)

    def remove_mode_callback(self, callback: Callable):
        """Remove a mode callback."""
        if callback in self._mode_callbacks:
            self._mode_callbacks.remove(callback)

    def _notify_mode_change(self, new_mode: VoiceMode):
        """Notify callbacks of mode change."""
        for callback in self._mode_callbacks:
            try:
                callback(new_mode)
            except Exception as e:
                print(f"[CommandParser] Mode callback error: {e}")

    def _notify_command(self, command: ParsedCommand):
        """Notify callbacks of detected command."""
        for callback in self._command_callbacks:
            try:
                callback(command)
            except Exception as e:
                print(f"[CommandParser] Command callback error: {e}")

    def _set_mode(self, mode: VoiceMode):
        """Set the current mode and notify callbacks."""
        if self._mode != mode:
            old_mode = self._mode
            self._mode = mode
            print(f"[CommandParser] Mode: {old_mode.value} -> {mode.value}")
            self._notify_mode_change(mode)

    def _detect_wake_word(self, text: str) -> Tuple[bool, str]:
        """Check if text contains a wake word.

        Returns:
            Tuple of (detected, remaining_text_after_wake_word)
        """
        text_lower = text.lower().strip()

        for wake_word in self.WAKE_WORDS_CLAUDE_CODE:
            # Check for wake word at start or anywhere in text
            if text_lower.startswith(wake_word):
                remaining = text[len(wake_word):].strip()
                # Remove leading punctuation/comma
                remaining = re.sub(r'^[,.\s]+', '', remaining)
                return True, remaining
            elif wake_word in text_lower:
                # Wake word in middle of text - extract what comes after
                idx = text_lower.find(wake_word)
                remaining = text[idx + len(wake_word):].strip()
                remaining = re.sub(r'^[,.\s]+', '', remaining)
                return True, remaining

        return False, text

    def _detect_end_phrase(self, text: str) -> bool:
        """Check if text contains an end phrase."""
        text_lower = text.lower().strip()
        return any(phrase in text_lower for phrase in self.END_PHRASES)

    def _clean_command(self, text: str) -> str:
        """Clean up command text for execution."""
        # Remove wake words if they got included
        text_lower = text.lower()
        for wake_word in self.WAKE_WORDS_CLAUDE_CODE:
            if text_lower.startswith(wake_word):
                text = text[len(wake_word):].strip()
                text_lower = text.lower()

        # Remove end phrases
        for end_phrase in self.END_PHRASES:
            if text_lower.endswith(end_phrase):
                text = text[:-len(end_phrase)].strip()
                text_lower = text.lower()

        # Clean up punctuation
        text = re.sub(r'^[,.\s]+', '', text)
        text = re.sub(r'[,.\s]+$', '', text)

        return text.strip()

    def process_transcript(self, transcript: str, is_final: bool) -> Optional[ParsedCommand]:
        """Process a transcript from STT.

        Args:
            transcript: The transcribed text
            is_final: Whether this is a final transcript

        Returns:
            ParsedCommand if a complete command was detected, None otherwise
        """
        if not transcript.strip():
            return None

        if self._mode == VoiceMode.IDLE:
            # Look for wake word
            detected, remaining = self._detect_wake_word(transcript)
            if detected:
                self._set_mode(VoiceMode.LISTENING)
                self._current_transcript = remaining

                # If there's text after the wake word in a final transcript,
                # it might be the complete command
                if is_final and remaining.strip():
                    # Check if it's a complete utterance (has end phrase or is a command)
                    if self._detect_end_phrase(remaining) or len(remaining.split()) >= 3:
                        return self._finalize_command(remaining)

            return None

        elif self._mode == VoiceMode.LISTENING:
            # Accumulate transcript
            if is_final:
                # This is a final transcript - likely the full command
                self._current_transcript = transcript
                _, remaining = self._detect_wake_word(transcript)

                # Check for end phrase or sufficient content
                if self._detect_end_phrase(remaining) or len(remaining.split()) >= 3:
                    return self._finalize_command(remaining)
                elif remaining.strip():
                    # Short command without end phrase - wait a bit more
                    # but if we have something, it might be complete
                    self._current_transcript = remaining
            else:
                # Interim result - just accumulate
                _, remaining = self._detect_wake_word(transcript)
                self._current_transcript = remaining

            return None

        elif self._mode == VoiceMode.PROCESSING:
            # Ignore transcripts while processing
            return None

        return None

    def _finalize_command(self, text: str) -> ParsedCommand:
        """Create a ParsedCommand and switch to processing mode."""
        self._set_mode(VoiceMode.PROCESSING)

        command_text = self._clean_command(text)
        is_claude_code = self._is_claude_code_command(command_text)

        command = ParsedCommand(
            raw_text=text,
            command=command_text,
            is_claude_code=is_claude_code,
            confidence=0.9 if is_claude_code else 0.7
        )

        self._notify_command(command)
        return command

    def _is_claude_code_command(self, command: str) -> bool:
        """Determine if command should go to Claude Code vs chat mode."""
        command_lower = command.lower()

        # Keywords that indicate Claude Code tasks
        code_keywords = [
            "create", "write", "make", "build", "generate", "add",
            "file", "script", "code", "function", "class", "component",
            "fix", "debug", "refactor", "update", "modify", "change",
            "delete", "remove", "install", "run", "execute", "test",
            "git", "commit", "push", "pull", "branch",
            "deploy", "configure", "setup", "initialize",
        ]

        return any(keyword in command_lower for keyword in code_keywords)

    def force_complete(self) -> Optional[ParsedCommand]:
        """Force complete the current command if in listening mode."""
        if self._mode == VoiceMode.LISTENING and self._current_transcript.strip():
            return self._finalize_command(self._current_transcript)
        return None

    def reset(self):
        """Reset parser to idle state."""
        self._current_transcript = ""
        self._set_mode(VoiceMode.IDLE)

    def command_completed(self):
        """Mark current command as completed, return to idle."""
        self._current_transcript = ""
        self._set_mode(VoiceMode.IDLE)

    def get_status(self) -> dict:
        """Get current parser status."""
        return {
            "mode": self._mode.value,
            "current_transcript": self._current_transcript,
            "callback_count": len(self._command_callbacks)
        }


# Singleton instance
command_parser_service = CommandParserService()
