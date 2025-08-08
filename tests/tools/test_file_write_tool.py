from pathlib import Path

import pytest

from aider.permissions import clear_permissions, grant_write
from aider.tools.base_tool import ToolError
from aider.tools.file_write_tool import FileWriteTool


def test_create_file(tmp_path: Path):
    clear_permissions()
    grant_write(tmp_path)

    target = tmp_path / "new.txt"
    msg = FileWriteTool().run(file_path=str(target), content="hello")
    assert target.read_text() == "hello"
    assert "created" in msg.lower()


def test_update_file(tmp_path: Path):
    clear_permissions()
    grant_write(tmp_path)

    target = tmp_path / "data.txt"
    target.write_text("old")
    msg = FileWriteTool().run(file_path=str(target), content="new")
    assert target.read_text() == "new"
    assert "updated" in msg.lower()


def test_requires_absolute(tmp_path: Path):
    grant_write(tmp_path)
    with pytest.raises(ToolError):
        FileWriteTool().run(file_path="relative/path.txt", content="x")


def test_permission_denied(tmp_path: Path):
    clear_permissions()  # no grant
    target = tmp_path / "secret.txt"
    with pytest.raises(ToolError):
        FileWriteTool().run(file_path=str(target), content="x")
