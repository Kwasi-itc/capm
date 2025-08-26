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
import shutil
import platform
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

from .base_tool import BaseTool, ToolError

# --------------- policy constants ------------------------------------------
MAX_OUTPUT_CHARS = 30_000
MAX_TIMEOUT_MS = 600_000             # 10 min
DEFAULT_TIMEOUT_MS = 600_000  # 10 min

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

    def __init__(self) -> None:
        """
        Initialize a new BashTool instance with its own persistent working
        directory state.
        """
        super().__init__()
        self._session_cwd: Path | None = None


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

        # track any temporary file created for long inline python
        tmp_path: str | None = None

        # working directory (persistent session)
        if cwd:
            path = Path(cwd).expanduser().resolve()
            if not path.is_dir():
                raise ToolError(f"cwd={path} is not a directory")
            BashTool._session_cwd = path

        workdir = BashTool._session_cwd or Path.cwd()

        # ----- choose shell program -----
        bash_exe = shutil.which("bash")
        if bash_exe:
            cmd_list = [bash_exe, "-lc", cmd]
        else:
            if platform.system() != "Windows":
                raise ToolError("`bash` executable not found on this system")
            # --- Windows fallback ------------------------------------
            cmd_fixed = cmd

            # Convert `python -c 'code'` → python -c "code"
            if cmd_fixed.lower().startswith("python -c '") and cmd_fixed.endswith("'"):
                head, code = cmd_fixed.split(" -c ", 1)
                code = code[1:-1]  # strip outer single quotes
                # Escape any embedded double-quotes so they survive cmd.exe
                code_escaped = code.replace('"', r'\"')
                cmd_fixed = f'{head} -c "{code_escaped}"'

            long_python_inline = (
                cmd_fixed.lower().startswith("python -c")
                and len(cmd_fixed) > 7500
            )

            if long_python_inline:
                # Spill code to a temporary file to avoid 8 k cmd.exe limit
                try:
                    _, _, py_code = shlex.split(cmd_fixed, posix=True)
                except Exception:  # noqa: BLE001
                    py_code = None

                if py_code:
                    tmp = tempfile.NamedTemporaryFile(
                        delete=False, suffix=".py", mode="w", encoding="utf-8"
                    )
                    tmp.write(py_code)
                    tmp.close()
                    tmp_path = tmp.name
                    cmd_list = [sys.executable, tmp_path]
                else:
                    cmd_list = ["cmd", "/c", cmd_fixed]
            else:
                cmd_list = ["cmd", "/c", cmd_fixed]

        # ----- execute -----
        start = time.time()
        try:
            proc = subprocess.run(
                cmd_list,
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )

            # ------- build nice output header & body up-front --------------
            elapsed_ms = int((time.time() - start) * 1000)
            combined = (proc.stdout or "") + (proc.stderr or "")
            out, total_lines = _truncate(combined)
            header = f"exit={proc.returncode}  lines={total_lines}  elapsed={elapsed_ms}ms"

            # Even on non-zero exit status, surface the captured output so the
            # user/LLM can see what actually happened instead of hiding it away.
            if proc.returncode != 0:
                if tmp_path:
                    Path(tmp_path).unlink(missing_ok=True)
                raise ToolError(
                    textwrap.dedent(
                        f"""\
                        {header}
                        ── output ──
                        {out}
                        """
                    ).rstrip()
                )
        except subprocess.TimeoutExpired:
            raise ToolError(f"Command timed out after {timeout_ms} ms") from None
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"Error running command: {exc}") from exc

        elapsed_ms = int((time.time() - start) * 1000)
        combined = (proc.stdout or "") + (proc.stderr or "")
        out, total_lines = _truncate(combined)

        header = f"exit={proc.returncode}  lines={total_lines}  elapsed={elapsed_ms}ms"
        result = textwrap.dedent(
            f"""\
            {header}
            ── output ──
            {out}
            """
        ).rstrip()
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
        return result
