import shutil
from pathlib import Path

import pytest

from aider.tools.memory_read_tool import MemoryReadTool
from aider.tools.memory_write_tool import MEMORY_DIR
from aider.tools.base_tool import ToolError


def setup_module(module):
    if MEMORY_DIR.exists():
        shutil.rmtree(MEMORY_DIR)


def test_read_specific_file():
    target = MEMORY_DIR / "notes" / "idea.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("hello")

    out = MemoryReadTool().run(file_path="notes/idea.txt")
    assert out == "hello"


def test_read_directory_index():
    (MEMORY_DIR / "index.md").write_text("# root index")
    (MEMORY_DIR / "misc.txt").write_text("blah")

    out = MemoryReadTool().run()
    assert "# root index" in out
    assert "misc.txt" in out


def test_security_outside_dir():
    with pytest.raises(ToolError):
        MemoryReadTool().run(file_path="../escape.txt")
