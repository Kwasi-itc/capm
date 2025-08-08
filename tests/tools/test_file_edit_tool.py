import pytest
from pathlib import Path

from aider.tools.file_edit_tool import FileEditTool, ToolError


def _mk(p: Path, text: str):
    p.write_text(text, encoding="utf-8")
    return p


# ---------------- happy paths ------------------------------------
def test_create(tmp_path: Path):
    f = tmp_path / "new.txt"
    out = FileEditTool().run(file_path=str(f), old_string="", new_string="hello")
    assert f.exists() and f.read_text() == "hello"
    assert "Created" in out


def test_update(tmp_path: Path):
    f = _mk(tmp_path / "code.py", "one two three")
    out = FileEditTool().run(file_path=str(f), old_string="two", new_string="TWO")
    assert f.read_text() == "one TWO three"
    assert "Updated" in out and "---" in out and "+++" in out


def test_delete(tmp_path: Path):
    f = _mk(tmp_path / "data.txt", "alpha\nbeta\ngamma")
    out = FileEditTool().run(file_path=str(f), old_string="beta\n", new_string="")
    assert f.read_text() == "alpha\ngamma"
    assert "Deleted" in out


# ---------------- edge cases / errors ----------------------------
def test_multiple_matches(tmp_path: Path):
    f = _mk(tmp_path / "dup.txt", "x y x")
    with pytest.raises(ToolError):
        FileEditTool().run(file_path=str(f), old_string="x", new_string="X")


def test_not_found(tmp_path: Path):
    f = _mk(tmp_path / "none.txt", "foo")
    with pytest.raises(ToolError):
        FileEditTool().run(file_path=str(f), old_string="bar", new_string="BAR")


def test_create_exists(tmp_path: Path):
    f = _mk(tmp_path / "exists.txt", "hi")
    with pytest.raises(ToolError):
        FileEditTool().run(file_path=str(f), old_string="", new_string="new")


def test_path_is_dir(tmp_path: Path):
    with pytest.raises(ToolError):
        FileEditTool().run(file_path=str(tmp_path), old_string="x", new_string="y")
