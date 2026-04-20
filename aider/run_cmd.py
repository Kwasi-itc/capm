import os
import platform
import re
import subprocess
import sys
from io import BytesIO

import pexpect
import psutil


def run_cmd(command, verbose=False, error_print=None, cwd=None):
    try:
        if sys.stdin.isatty() and hasattr(pexpect, "spawn") and platform.system() != "Windows":
            return run_cmd_pexpect(command, verbose, cwd)

        return run_cmd_subprocess(command, verbose, cwd)
    except OSError as e:
        error_message = f"Error occurred while running command '{command}': {str(e)}"
        if error_print is None:
            print(error_message)
        else:
            error_print(error_message)
        return 1, error_message


def get_windows_parent_process_name():
    try:
        current_process = psutil.Process()
        while True:
            parent = current_process.parent()
            if parent is None:
                break
            parent_name = parent.name().lower()
            if parent_name in ["powershell.exe", "cmd.exe"]:
                return parent_name
            current_process = parent
        return None
    except Exception:
        return None


def run_cmd_subprocess(command, verbose=False, cwd=None, encoding=sys.stdout.encoding):
    if verbose:
        print("Using run_cmd_subprocess:", command)

    try:
        shell = os.environ.get("SHELL", "/bin/sh")
        parent_process = None

        # Determine the appropriate shell
        if platform.system() == "Windows":
            parent_process = get_windows_parent_process_name()
            if parent_process == "powershell.exe":
                command = f"powershell -Command {command}"

        if verbose:
            print("Running command:", command)
            print("SHELL:", shell)
            if platform.system() == "Windows":
                print("Parent process:", parent_process)

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            encoding=encoding,
            errors="replace",
            bufsize=0,  # Set bufsize to 0 for unbuffered output
            universal_newlines=True,
            cwd=cwd,
        )

        output = []
        while True:
            chunk = process.stdout.read(1)
            if not chunk:
                break
            print(chunk, end="", flush=True)  # Print the chunk in real-time
            output.append(chunk)  # Store the chunk for later use

        process.wait()
        return process.returncode, "".join(output)
    except Exception as e:
        return 1, str(e)


def _strip_ansi_escape_sequences(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    # Pattern to match ANSI escape sequences
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def _deduplicate_interactive_output(text: str) -> str:
    """
    Remove duplicate lines from interactive output that result from menu redraws.
    For interactive prompts with arrow keys, the same menu state can appear multiple times.
    """
    if not text:
        return text
    
    lines = text.splitlines()
    if not lines:
        return text
    
    # Keep track of recent lines to detect duplicates
    # Interactive menus often redraw the same content, so we remove consecutive duplicates
    cleaned_lines = []
    prev_line = None
    duplicate_window = []  # Keep a small window to catch near-duplicates
    
    for line in lines:
        # Strip ANSI sequences for comparison
        clean_line = _strip_ansi_escape_sequences(line).strip()
        
        # Skip if this is the same as the previous line (after cleaning)
        if clean_line == prev_line:
            continue
        
        # Skip if this line appears in the recent window (likely a redraw)
        is_duplicate = False
        for window_line in duplicate_window[-10:]:  # Check last 10 lines
            if _strip_ansi_escape_sequences(window_line).strip() == clean_line:
                is_duplicate = True
                break
        
        if is_duplicate and clean_line:  # Only skip non-empty duplicates
            continue
        
        cleaned_lines.append(line)
        prev_line = clean_line
        duplicate_window.append(line)
        if len(duplicate_window) > 20:
            duplicate_window.pop(0)
    
    return '\n'.join(cleaned_lines)


def run_cmd_pexpect(command, verbose=False, cwd=None):
    """
    Run a shell command interactively using pexpect, capturing all output.

    :param command: The command to run as a string.
    :param verbose: If True, print output in real-time.
    :return: A tuple containing (exit_status, output)
    """
    if verbose:
        print("Using run_cmd_pexpect:", command)

    output = BytesIO()
    recent_lines = []  # Track recent lines to detect duplicate menu redraws
    max_recent_lines = 50

    def output_filter(data):
        """
        Filter output to prevent duplicate menu displays.
        For interactive menus that redraw, we filter out duplicate states.
        """
        # Always capture for return value
        output.write(data)
        
        # Convert to string for line-by-line analysis
        try:
            text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else str(data)
        except Exception:
            text = str(data)
        
        # Split into lines for analysis
        lines = text.splitlines(keepends=True) if text else []
        
        # Filter lines to avoid displaying duplicates
        filtered_lines = []
        for line in lines:
            clean_line = _strip_ansi_escape_sequences(line).strip()
            
            # Skip empty lines
            if not clean_line:
                filtered_lines.append(line)
                continue
            
            # Check if this line (or very similar) appeared recently
            is_duplicate = False
            for recent in recent_lines[-20:]:  # Check last 20 lines
                if _strip_ansi_escape_sequences(recent).strip() == clean_line:
                    is_duplicate = True
                    break
            
            if not is_duplicate or not clean_line:
                filtered_lines.append(line)
                recent_lines.append(line)
                if len(recent_lines) > max_recent_lines:
                    recent_lines.pop(0)
        
        # Return filtered data for display, or original if filtering removed nothing
        if len(filtered_lines) < len(lines):
            filtered_text = ''.join(filtered_lines)
            return filtered_text.encode("utf-8") if isinstance(data, bytes) else filtered_text
        
        return data

    try:
        # Use the SHELL environment variable, falling back to /bin/sh if not set
        shell = os.environ.get("SHELL", "/bin/sh")
        if verbose:
            print("With shell:", shell)

        if os.path.exists(shell):
            # Use the shell from SHELL environment variable
            if verbose:
                print("Running pexpect.spawn with shell:", shell)
            child = pexpect.spawn(shell, args=["-i", "-c", command], encoding="utf-8", cwd=cwd)
        else:
            # Fall back to spawning the command directly
            if verbose:
                print("Running pexpect.spawn without shell.")
            child = pexpect.spawn(command, encoding="utf-8", cwd=cwd)

        # Use output_filter to prevent duplicate displays during interact
        # while still capturing everything for return value
        child.interact(output_filter=output_filter)

        # Wait for the command to finish and get the exit status
        child.close()
        
        # Decode the captured output (has everything, including duplicates)
        raw_output = output.getvalue().decode("utf-8", errors="replace")
        
        # Clean up duplicate interactive menu redraws from captured output
        cleaned_output = _deduplicate_interactive_output(raw_output)
        
        return child.exitstatus, cleaned_output

    except (pexpect.ExceptionPexpect, TypeError, ValueError) as e:
        error_msg = f"Error running command {command}: {e}"
        return 1, error_msg
