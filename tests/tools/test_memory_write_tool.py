import shutil
from pathlib import Path

import pytest

from aider.tools.memory_write_tool import MemoryWriteTool, MEMORY_DIR
from aider.tools.base_tool import ToolError


def setup_module(module):
    # Ensure a clean slate before running tests
    if MEMORY_DIR.exists():
        shutil.rmtree(MEMORY_DIR)


def test_memory_write_basic():
    out = MemoryWriteTool().run(file_path="notes/info.txt", content="hello")
    assert out == "Saved"
    target = MEMORY_DIR / "notes" / "info.txt"
    assert target.exists()
    assert target.read_text() == "hello"


def test_memory_write_overwrite():
    target = MEMORY_DIR / "overwrite.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("old")

    MemoryWriteTool().run(file_path="overwrite.txt", content="new")
    assert target.read_text() == "new"


def test_memory_write_outside_dir():
    with pytest.raises(ToolError):
        MemoryWriteTool().run(file_path="../escape.txt", content="x")
