"""
BashTool – execute ONE shell command inside Bash and return its output.

This tool wraps the existing `/run` command functionality (via `cmd_run`),
delegating all command execution to `aider.run_cmd.run_cmd()` which handles
shell selection, platform differences, and real-time output streaming.

Safety & limits
---------------
• BANNED_COMMANDS are rejected outright (security / policy).
• New-lines in *cmd* are forbidden – join multiple commands with ';' or '&&'.
• Output is truncated to MAX_OUTPUT_CHARS (30 000) with a middle-ellipsis.
"""
from __future__ import annotations

import shlex
import textwrap
import time
from pathlib import Path
from typing import Any, Dict

from .base_tool import BaseTool, ToolError
from aider.run_cmd import run_cmd

# --------------- policy constants ------------------------------------------
MAX_OUTPUT_CHARS = 30_000

BANNED_COMMANDS = {
    "alias",
    "curl",
    "curlie",
    "wget",
    "axel",
    "aria2c",
    "nc",
    "telnet",
    "lynx",
    "w3m",
    "links",
    "httpie",
    "xh",
    "http-prompt",
    "chrome",
    "firefox",
    "safari",
}


# --------------- helpers ----------------------------------------------------
def _truncate(text: str) -> tuple[str, int]:
    """Return possibly-truncated text and original line-count."""
    lines = text.splitlines()
    if len(text) <= MAX_OUTPUT_CHARS:
        return text.rstrip(), len(lines)

    half = MAX_OUTPUT_CHARS // 2
    head, tail = text[:half], text[-half:]
    middle_lines = text[half:-half].splitlines()
    ellipsis = f"\n\n... [{len(middle_lines)} lines truncated] ...\n\n"
    return (head + ellipsis + tail).rstrip(), len(lines)


def _first_token(cmd: str) -> str:
    try:
        return shlex.split(cmd, posix=True)[0]
    except ValueError:
        return ""


# --------------- tool implementation ---------------------------------------
class BashTool(BaseTool):
    name = "bash"
    description = (
        "Execute a shell command and return its output. Output is the "
        "combined stdout/stderr (truncated to ~30 000 chars)."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "cmd": {
                "type": "string",
                "description": "Single shell command to execute (no newlines).",
            },
            "cwd": {
                "type": "string",
                "description": "Optional working directory for the command.",
            },
        },
        "required": ["cmd"],
        "additionalProperties": False,
    }

    # ---------------- spinner control -------------------------------------
    def wants_spinner(self) -> bool:
        """Disable waiting spinner – BashTool streams its own live output."""
        return False

    # ---------------- main entry point ------------------------------------
    def run(
        self,
        *,
        cmd: str,
        cwd: str | None = None,
    ) -> str:
        # ----- basic validation -----
        if "\n" in cmd:
            raise ToolError("Command must not contain newline characters; use ';' or '&&'.")

        token = _first_token(cmd)
        if token in BANNED_COMMANDS:
            raise ToolError(f"The command '{token}' is disallowed for security reasons.")

        # ----- determine working directory -----
        # Use provided cwd, fall back to coder's root if available, otherwise current directory
        if cwd:
            workdir = Path(cwd).expanduser().resolve()
            if not workdir.is_dir():
                raise ToolError(f"cwd={workdir} is not a directory")
        elif hasattr(self, "coder") and self.coder and hasattr(self.coder, "root") and self.coder.root:
            workdir = Path(self.coder.root)
        else:
            workdir = Path.cwd()

        # ----- execute using run_cmd (same as /run command) -----
        start = time.time()
        
        # Use run_cmd directly, just like cmd_run does - it handles all shell/platform logic
        exit_code, output = run_cmd(
            cmd,
            verbose=False,
            error_print=None,  # Don't print errors here, we handle them below
            cwd=str(workdir),
        )
        elapsed_ms = int((time.time() - start) * 1000)

        # Handle None output (shouldn't happen with current run_cmd, but be safe)
        if output is None:
            output = ""

        # ----- format output -----
        out, total_lines = _truncate(output)
        header = f"exit={exit_code}  lines={total_lines}  elapsed={elapsed_ms}ms"

        return textwrap.dedent(
            f"""\
            {header}
            ── output ──
            {out}
            """
        ).rstrip()
