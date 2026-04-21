import shutil
import subprocess
import sys
from pathlib import Path


def _quote_for_shell(cmd):
    return subprocess.list2cmdline([str(part) for part in cmd])


def _run_codex_command(cmd, cwd=None):
    if sys.platform == "win32":
        return subprocess.call(_quote_for_shell(cmd), cwd=cwd, shell=True)

    return subprocess.call(cmd, cwd=cwd)


def _read_message_file(message_file, io, encoding):
    try:
        return Path(message_file).read_text(encoding=encoding)
    except OSError as err:
        io.tool_error(f"Error reading message file: {err}")


def _build_codex_args(args, io):
    cmd = [args.codex_command]

    if args.codex_model:
        cmd += ["-m", args.codex_model]

    message = args.message
    if args.message_file:
        message = _read_message_file(args.message_file, io, args.encoding)
        if message is None:
            return

    if message:
        cmd.append(message)

    return cmd


def run_codex_backend(args, io, cwd=None):
    """
    Launch the official Codex CLI as a separate assistant backend.

    This intentionally delegates the agent loop to Codex instead of trying to
    reuse Codex credentials inside the native LiteLLM path.
    """
    codex_path = shutil.which(args.codex_command)
    if not codex_path:
        io.tool_error("Codex CLI is not installed or is not on PATH.")
        io.tool_output("Install it with: npm i -g @openai/codex")
        return 1

    if not args.codex_skip_login:
        io.tool_output("Starting Codex sign-in. Use your ChatGPT/Codex account if prompted.")
        try:
            login_status = _run_codex_command([codex_path, "login"], cwd=cwd)
        except OSError as err:
            io.tool_error(f"Unable to launch Codex login: {err}")
            return 1
        if login_status:
            io.tool_error(f"Codex login failed with exit code {login_status}.")
            return login_status

    codex_cmd = _build_codex_args(args, io)
    if not codex_cmd:
        return 1
    codex_cmd[0] = codex_path

    io.tool_output("Starting Codex CLI backend.")
    try:
        return _run_codex_command(codex_cmd, cwd=cwd)
    except OSError as err:
        io.tool_error(f"Unable to launch Codex CLI: {err}")
        return 1
