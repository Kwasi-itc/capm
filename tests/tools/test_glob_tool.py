import os
import time
from pathlib import Path

import pytest

from aider.tools.glob_tool import GlobTool, MAX_RESULTS
from aider.tools.base_tool import ToolError


def make_file(tmp: Path, name: str, mtime_shift: int = 0):
    p = tmp / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x")
    if mtime_shift:
        past = time.time() - mtime_shift
        os.utime(p, (past, past))
    return p


def test_glob_basic(tmp_path: Path):
    make_file(tmp_path, "a.py")
    make_file(tmp_path, "b.js")

    out = GlobTool().run(pattern="*.py", path=str(tmp_path))
    assert "Found 1 file" in out
    assert "a.py" in out
    assert "b.js" not in out


def test_glob_recursive(tmp_path: Path):
    make_file(tmp_path / "src", "foo.ts")
    make_file(tmp_path / "src" / "sub", "bar.ts")

    out = GlobTool().run(pattern="src/**/*.ts", path=str(tmp_path))
    assert "foo.ts" in out and "bar.ts" in out


def test_glob_path_not_dir(tmp_path: Path):
    file_path = make_file(tmp_path, "single.txt")
    with pytest.raises(ToolError):
        GlobTool().run(pattern="*.txt", path=str(file_path))


def test_glob_truncation(tmp_path: Path):
    for i in range(MAX_RESULTS + 7):
        make_file(tmp_path, f"f{i}.txt")
    out = GlobTool().run(pattern="*.txt", path=str(tmp_path))
    assert len(out.splitlines()) == MAX_RESULTS + 1
    assert "truncated" in out.lower()


def test_glob_ordering(tmp_path: Path):
    make_file(tmp_path, "old.txt", mtime_shift=60)
    newest = make_file(tmp_path, "new.txt", mtime_shift=5)
    out = GlobTool().run(pattern="*.txt", path=str(tmp_path))
    assert out.splitlines()[1] == newest.name
