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
import itertools
import threading
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
            "progress": {
                "type": "boolean",
                "description": "Show a live spinner/progress indicator while the command runs.",
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
    def run(
        self,
        *,
        cmd: str,
        timeout: int | None = None,
        cwd: str | None = None,
        progress: bool = False,
    ) -> str:
        # ----- basic validation -----
        if "\n" in cmd:
            raise ToolError("Command must not contain newline characters; use ';' or '&&'.")

        token = _first_token(cmd)
        if token in BANNED_COMMANDS:
            raise ToolError(f"The command '{token}' is disallowed for security reasons.")

        timeout_ms = timeout if timeout is not None else DEFAULT_TIMEOUT_MS
        timeout_ms = min(max(timeout_ms, 1), MAX_TIMEOUT_MS)
        timeout_s = timeout_ms / 1000.0

        # -------- optional spinner/progress indicator ---------
        stop_spinner: threading.Event | None = None
        spinner_thread: threading.Thread | None = None
        if progress and sys.stdout.isatty():
            stop_spinner = threading.Event()

            def _spin(ev: threading.Event) -> None:
                for ch in itertools.cycle("|/-\\"):
                    if ev.is_set():
                        break
                    sys.stdout.write(f"\rRunning… {ch}")
                    sys.stdout.flush()
                    time.sleep(0.1)
                sys.stdout.write("\r" + " " * 20 + "\r")
                sys.stdout.flush()

            spinner_thread = threading.Thread(target=_spin, args=(stop_spinner,), daemon=True)
            spinner_thread.start()

        # track any temporary file created for long inline python
        tmp_path: str | None = None

        # working directory (persistent session)
        if cwd:
            path = Path(cwd).expanduser().resolve()
            if not path.is_dir():
                raise ToolError(f"cwd={path} is not a directory")
            self._session_cwd = path

        workdir = self._session_cwd or Path.cwd()

        # ----- choose shell program -----
        bash_exe = shutil.which("bash")
        if bash_exe:
            cmd_list = [bash_exe, "-lc", cmd]
        else:
            # Fail fast when the requested command explicitly starts with `bash`
            # but no Bash executable is available.  This avoids the confusing
            # "'bash' is not recognized as an internal or external command" error
            # that would otherwise come from cmd.exe.
            if token == "bash":
                raise ToolError(
                    "`bash` executable not found on this Windows system. "
                    "Install Git Bash, enable the Windows Subsystem for Linux (WSL) "
                    "or rewrite the command using native Windows tools."
                )
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
            # --- live streaming -------------------------------------------------
            #
            # Stream stdout/stderr to the user in real-time so long-running
            # programs like “npm run dev” immediately show their output while
            # they execute.  We still capture everything so it can be returned
            # to the LLM once the command finishes or times-out.
            #
            output_lines: list[str] = []
            proc = subprocess.Popen(
                cmd_list,
                cwd=workdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            deadline = start + timeout_s
            try:
                for line in proc.stdout:
                    # Stop the spinner on first real output
                    if line and stop_spinner and not stop_spinner.is_set():
                        stop_spinner.set()
                        spinner_thread.join()

                    sys.stdout.write(line)
                    sys.stdout.flush()
                    output_lines.append(line)

                    if time.time() > deadline:
                        proc.kill()
                        raise subprocess.TimeoutExpired(cmd_list, timeout_s)
                # ensure the process has exited (raises on timeout)
                proc.wait(timeout=max(0, deadline - time.time()))
            finally:
                if proc.stdout:
                    proc.stdout.close()

            # if no output at all (eg. silent command) stop the spinner now
            if stop_spinner and not stop_spinner.is_set():
                stop_spinner.set()
                spinner_thread.join()

            # stop spinner once process has finished
            if stop_spinner:
                stop_spinner.set()
                spinner_thread.join()

            # ------- build nice output header & body up-front --------------
            elapsed_ms = int((time.time() - start) * 1000)
            combined = "".join(output_lines)
            out, total_lines = _truncate(combined)
            header = f"exit={proc.returncode}  lines={total_lines}  elapsed={elapsed_ms}ms"

            # On non-zero exit we still return the captured output instead of
            # raising an error. The LLM can inspect the result and decide what
            # to do next.
            if proc.returncode != 0:
                if tmp_path:
                    Path(tmp_path).unlink(missing_ok=True)
                return textwrap.dedent(
                    f"""\
                    {header}
                    ── output ──
                    {out}
                    """
                ).rstrip()
        except subprocess.TimeoutExpired:
            if stop_spinner:
                stop_spinner.set()
                spinner_thread.join()
            # Return a plain string instead of throwing so the LLM can handle it.
            return f"Command timed out after {timeout_ms} ms"
        except Exception as exc:  # noqa: BLE001
            if stop_spinner:
                stop_spinner.set()
                spinner_thread.join()
            # Surface the error text as the tool’s result instead of raising.
            return f"Error running command: {exc}"

        elapsed_ms = int((time.time() - start) * 1000)
        combined = "".join(output_lines)
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
