"""
BashTool – execute ONE shell command inside Bash and return its output.

Safety & limits
---------------
• BANNED_COMMANDS are rejected outright (security / policy).
• New-lines in *cmd* are forbidden – join multiple commands with ';' or '&&'.
• Default timeout is 30 min; user may pass a shorter value (milliseconds) up to
  MAX_TIMEOUT_MS (10 min) – longer values are capped.
• Output is truncated to MAX_OUTPUT_CHARS (30 000) with a middle-ellipsis.
"""
from __future__ import annotations

import shlex
import subprocess
import textwrap
import time
from pathlib import Path
from typing import Any, Dict

from .base_tool import BaseTool, ToolError

# --------------- policy constants ------------------------------------------
MAX_OUTPUT_CHARS = 30_000
MAX_TIMEOUT_MS = 600_000             # 10 min
DEFAULT_TIMEOUT_MS = 30 * 60 * 1000  # 30 min

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
        "Execute a Bash command in a persistent shell session. Output is the "
        "combined stdout/stderr (truncated to ~30 000 chars). A timeout in "
        "milliseconds can be supplied (max 600 000 ms)."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "cmd": {
                "type": "string",
                "description": "Single Bash command to execute (no newlines).",
            },
            "timeout": {
                "type": "integer",
                "description": f"Optional timeout in ms (≤ {MAX_TIMEOUT_MS}).",
            },
            "cwd": {
                "type": "string",
                "description": "Optional working directory for the command.",
            },
        },
        "required": ["cmd"],
        "additionalProperties": False,
    }

    # persistent working directory across calls
    _session_cwd: Path | None = None

    # ---------------- main entry point ------------------------------------
    def run(self, *, cmd: str, timeout: int | None = None, cwd: str | None = None) -> str:
        # ----- basic validation -----
        if "\n" in cmd:
            raise ToolError("Command must not contain newline characters; use ';' or '&&'.")

        token = _first_token(cmd)
        if token in BANNED_COMMANDS:
            raise ToolError(f"The command '{token}' is disallowed for security reasons.")

        timeout_ms = timeout if timeout is not None else DEFAULT_TIMEOUT_MS
        timeout_ms = min(max(timeout_ms, 1), MAX_TIMEOUT_MS)
        timeout_s = timeout_ms / 1000.0

        # working directory (persistent session)
        if cwd:
            path = Path(cwd).expanduser().resolve()
            if not path.is_dir():
                raise ToolError(f"cwd={path} is not a directory")
            BashTool._session_cwd = path

        workdir = BashTool._session_cwd or Path.cwd()

        # ----- execute -----
        start = time.time()
        try:
            proc = subprocess.run(
                ["bash", "-lc", cmd],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired:
            raise ToolError(f"Command timed out after {timeout_ms} ms") from None
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"Error running command: {exc}") from exc

        elapsed_ms = int((time.time() - start) * 1000)
        combined = (proc.stdout or "") + (proc.stderr or "")
        out, total_lines = _truncate(combined)

        header = f"exit={proc.returncode}  lines={total_lines}  elapsed={elapsed_ms}ms"
        return textwrap.dedent(
            f"""\
            {header}
            ── output ──
            {out}
            """
        ).rstrip()
