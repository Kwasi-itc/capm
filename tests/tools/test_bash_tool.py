import pytest
from pathlib import Path

from aider.tools.bash_tool import BashTool, ToolError, MAX_OUTPUT_CHARS


def test_echo(tmp_path: Path):
    out = BashTool().run(cmd="echo hello bash")
    assert "exit=0" in out and "hello bash" in out


def test_banned_command(tmp_path: Path):
    with pytest.raises(ToolError):
        BashTool().run(cmd="curl http://example.com")


def test_timeout(tmp_path: Path):
    with pytest.raises(ToolError):
        BashTool().run(cmd="sleep 2", timeout=200)  # 0.2 s


def test_truncation(tmp_path: Path):
    big = "x" * (MAX_OUTPUT_CHARS + 5000)
    out = BashTool().run(cmd=f"python -c 'print({big!r})'")
    assert "truncated" in out.lower()
