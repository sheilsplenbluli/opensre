"""Shell command execution tool for opensre.

Allows running arbitrary shell commands as part of an SRE workflow graph.
Use with caution — commands run with the same privileges as the opensre process.
"""

import shlex
import shutil
import subprocess
from typing import Any

from opensre.tools.base import BaseTool, ToolResult


class ShellTool(BaseTool):
    """Run a shell command and capture its output.

    Parameters accepted in ``params``:
        - ``command`` (str, required): The shell command to execute.
        - ``timeout`` (int, optional): Max seconds to wait. Defaults to 30.
        - ``shell`` (bool, optional): Run via shell interpreter. Defaults to False
          (safer — command is split with shlex). Set True only when you need
          shell features like pipes or glob expansion.
    """

    my_tool_name: str = "shell"

    # ------------------------------------------------------------------
    # Availability
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Always available — every POSIX-like system has a shell."""
        return shutil.which("sh") is not None

    # ------------------------------------------------------------------
    # Parameter extraction
    # ------------------------------------------------------------------

    def extract_params(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Validate and normalise raw params coming from the graph node."""
        command = raw.get("command")
        if not command or not isinstance(command, str):
            raise ValueError("ShellTool requires a non-empty 'command' string param")

        timeout = raw.get("timeout", 30)
        if not isinstance(timeout, int) or timeout <= 0:
            raise ValueError("'timeout' must be a positive integer")

        use_shell = bool(raw.get("shell", False))

        return {
            "command": command,
            "timeout": timeout,
            "shell": use_shell,
        }

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self, params: dict[str, Any]) -> ToolResult:
        """Execute the shell command and return a :class:`ToolResult`.

        Returns a successful result when the process exits with code 0.
        Non-zero exit codes are treated as failures; the stderr output is
        included in the error message to make debugging easier.
        """
        command: str = params["command"]
        timeout: int = params["timeout"]
        use_shell: bool = params["shell"]

        # Split into a list when not using the shell interpreter so that
        # arguments with spaces are handled correctly.
        cmd = command if use_shell else shlex.split(command)

        try:
            proc = subprocess.run(
                cmd,
                shell=use_shell,  # noqa: S603
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout}s: {command}",
            )
        except FileNotFoundError as exc:
            return ToolResult(
                success=False,
                output="",
                error=f"Executable not found: {exc}",
            )
        except OSError as exc:
            return ToolResult(
                success=False,
                output="",
                error=f"OS error while running command: {exc}",
            )

        if proc.returncode != 0:
            return ToolResult(
                success=False,
                output=proc.stdout,
                error=(
                    f"Command exited with code {proc.returncode}.\n"
                    f"stderr: {proc.stderr.strip()}"
                ),
            )

        return ToolResult(success=True, output=proc.stdout, error="")
