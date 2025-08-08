from pathlib import Path

import pytest

from aider.permissions import clear_permissions, grant_read
from aider.tools.ls_tool import LsTool, MAX_FILES, TRUNCATED_MSG
from aider.tools.base_tool import ToolError


# helpers ---------------------------------------------------------------------
def make_dir(base: Path, rel: str) -> Path:
    p = base / rel
    p.mkdir(parents=True, exist_ok=True)
    return p


def make_file(base: Path, rel: str):
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x")
    return p


# tests -----------------------------------------------------------------------
def test_ls_basic(tmp_path: Path):
    clear_permissions()
    grant_read(tmp_path)

    make_file(tmp_path, "a.py")
    make_dir(tmp_path, "dir")
    make_file(tmp_path, "dir/b.txt")

    out = LsTool().run(path=str(tmp_path))
    assert "- a.py" in out
    assert "- dir/" in out
    assert "- b.txt" in out


def test_ls_requires_absolute(tmp_path: Path):
    clear_permissions()
    grant_read(tmp_path)

    with pytest.raises(ToolError):
        LsTool().run(path="relative/path")


def test_ls_permission_denied(tmp_path: Path):
    clear_permissions()  # no permission granted

    with pytest.raises(ToolError):
        LsTool().run(path=str(tmp_path))


def test_ls_skip_rules(tmp_path: Path):
    clear_permissions()
    grant_read(tmp_path)

    make_file(tmp_path, ".secret")
    make_file(tmp_path / "__pycache__", "ignored.py")

    out = LsTool().run(path=str(tmp_path))
    assert ".secret" not in out
    assert "__pycache__" not in out


def test_ls_truncation(tmp_path: Path):
    clear_permissions()
    grant_read(tmp_path)

    for i in range(MAX_FILES + 5):
        make_file(tmp_path, f"f{i}.txt")

    out = LsTool().run(path=str(tmp_path))
    assert TRUNCATED_MSG.splitlines()[0] in out
