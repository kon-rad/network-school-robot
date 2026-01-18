"""
Claude Code CLI Executor Service.
Manages subprocess execution of Claude Code commands.
"""
import asyncio
import shutil
from typing import AsyncGenerator, Callable, List, Optional
from dataclasses import dataclass
from enum import Enum


class ExecutionStatus(Enum):
    """Status of a Claude Code execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """Result of a Claude Code execution."""
    command: str
    status: ExecutionStatus
    output: str
    error: Optional[str] = None


class ClaudeCodeService:
    """Executes commands via Claude Code CLI."""

    def __init__(self):
        self._current_process: Optional[asyncio.subprocess.Process] = None
        self._is_executing = False
        self._output_callbacks: List[Callable] = []
        self._status_callbacks: List[Callable] = []

    def is_executing(self) -> bool:
        """Check if currently executing a command."""
        return self._is_executing

    def is_available(self) -> bool:
        """Check if Claude Code CLI is available."""
        return shutil.which("claude") is not None

    def add_output_callback(self, callback: Callable):
        """Register callback for streaming output."""
        self._output_callbacks.append(callback)

    def remove_output_callback(self, callback: Callable):
        """Remove an output callback."""
        if callback in self._output_callbacks:
            self._output_callbacks.remove(callback)

    def add_status_callback(self, callback: Callable):
        """Register callback for status changes."""
        self._status_callbacks.append(callback)

    def remove_status_callback(self, callback: Callable):
        """Remove a status callback."""
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)

    async def _notify_output(self, line: str):
        """Notify callbacks of output line."""
        for callback in self._output_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(line)
                else:
                    callback(line)
            except Exception as e:
                print(f"[ClaudeCode] Output callback error: {e}")

    async def _notify_status(self, status: ExecutionStatus, details: str = ""):
        """Notify callbacks of status change."""
        for callback in self._status_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(status, details)
                else:
                    callback(status, details)
            except Exception as e:
                print(f"[ClaudeCode] Status callback error: {e}")

    async def execute_command(self, command: str) -> ExecutionResult:
        """Execute a command via Claude Code CLI.

        Args:
            command: The natural language command for Claude Code

        Returns:
            ExecutionResult with the command output
        """
        if self._is_executing:
            return ExecutionResult(
                command=command,
                status=ExecutionStatus.FAILED,
                output="",
                error="Another command is already executing"
            )

        if not self.is_available():
            return ExecutionResult(
                command=command,
                status=ExecutionStatus.FAILED,
                output="",
                error="Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
            )

        self._is_executing = True
        output_lines = []

        try:
            await self._notify_status(ExecutionStatus.RUNNING, f"Executing: {command[:50]}...")

            # Execute Claude Code with the prompt
            # Use --dangerously-skip-permissions for non-interactive mode
            self._current_process = await asyncio.create_subprocess_exec(
                "claude",
                "-p", command,
                "--output-format", "text",
                "--dangerously-skip-permissions",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                stdin=asyncio.subprocess.DEVNULL
            )

            # Stream output
            while True:
                if self._current_process.stdout is None:
                    break

                line = await self._current_process.stdout.readline()
                if not line:
                    break

                decoded_line = line.decode().rstrip()
                if decoded_line:
                    output_lines.append(decoded_line)
                    await self._notify_output(decoded_line)

            # Wait for process to complete
            await self._current_process.wait()

            return_code = self._current_process.returncode
            output = "\n".join(output_lines)

            if return_code == 0:
                await self._notify_status(ExecutionStatus.COMPLETED, "Command completed successfully")
                return ExecutionResult(
                    command=command,
                    status=ExecutionStatus.COMPLETED,
                    output=output
                )
            else:
                await self._notify_status(ExecutionStatus.FAILED, f"Exit code: {return_code}")
                return ExecutionResult(
                    command=command,
                    status=ExecutionStatus.FAILED,
                    output=output,
                    error=f"Command failed with exit code {return_code}"
                )

        except asyncio.CancelledError:
            await self._notify_status(ExecutionStatus.CANCELLED, "Command cancelled")
            return ExecutionResult(
                command=command,
                status=ExecutionStatus.CANCELLED,
                output="\n".join(output_lines),
                error="Command was cancelled"
            )
        except Exception as e:
            await self._notify_status(ExecutionStatus.FAILED, str(e))
            return ExecutionResult(
                command=command,
                status=ExecutionStatus.FAILED,
                output="\n".join(output_lines),
                error=str(e)
            )
        finally:
            self._is_executing = False
            self._current_process = None

    async def execute_command_streaming(self, command: str) -> AsyncGenerator[str, None]:
        """Execute a command and stream output line by line.

        Args:
            command: The natural language command for Claude Code

        Yields:
            Output lines as they are produced
        """
        if self._is_executing:
            yield "Error: Another command is already executing"
            return

        if not self.is_available():
            yield "Error: Claude Code CLI not found"
            return

        self._is_executing = True

        try:
            self._current_process = await asyncio.create_subprocess_exec(
                "claude",
                "-p", command,
                "--output-format", "text",
                "--dangerously-skip-permissions",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                stdin=asyncio.subprocess.DEVNULL
            )

            while True:
                if self._current_process.stdout is None:
                    break

                line = await self._current_process.stdout.readline()
                if not line:
                    break

                decoded_line = line.decode().rstrip()
                if decoded_line:
                    yield decoded_line

            await self._current_process.wait()

        except Exception as e:
            yield f"Error: {str(e)}"
        finally:
            self._is_executing = False
            self._current_process = None

    async def cancel_execution(self) -> dict:
        """Cancel the currently executing command."""
        if not self._is_executing or not self._current_process:
            return {"success": False, "message": "No command executing"}

        try:
            self._current_process.terminate()
            await asyncio.sleep(0.5)

            if self._current_process.returncode is None:
                self._current_process.kill()

            await self._notify_status(ExecutionStatus.CANCELLED, "Command cancelled by user")
            return {"success": True, "message": "Command cancelled"}

        except Exception as e:
            return {"success": False, "message": f"Cancel failed: {str(e)}"}

    def get_status(self) -> dict:
        """Get current service status."""
        return {
            "available": self.is_available(),
            "executing": self._is_executing,
            "callback_count": len(self._output_callbacks)
        }


# Singleton instance
claude_code_service = ClaudeCodeService()
