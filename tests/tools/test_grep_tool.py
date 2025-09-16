import os
import time
from pathlib import Path

import pytest

from aider.tools.grep_tool import GrepTool, MAX_RESULTS
from aider.tools.base_tool import ToolError


# ------------- helpers --------------------------------------------------------
def make_file(tmp_path: Path, name: str, content: bytes = b"", mtime_shift: int = 0) -> Path:
    """
    Create a file under ``tmp_path`` with the given content.
    Optionally shift its modification time ``mtime_shift`` seconds into the past
    so we can test sort-by-mtime behaviour.
    """
    fpath = tmp_path / name
    fpath.write_bytes(content)
    if mtime_shift:
        past = time.time() - mtime_shift
        os.utime(fpath, (past, past))
    return fpath


# ------------- happy paths ----------------------------------------------------
def test_basic_match(tmp_path: Path):
    make_file(tmp_path, "a.txt", b"hello world")
    make_file(tmp_path, "b.txt", b"goodbye")

    out = GrepTool().run(pattern="hello", path=str(tmp_path))
    assert "Found 1 file" in out
    assert "a.txt" in out
    assert "b.txt" not in out


def test_include_glob(tmp_path: Path):
    make_file(tmp_path, "foo.py", b"regex inside")
    make_file(tmp_path, "bar.js", b"regex inside")

    out = GrepTool().run(pattern="regex", path=str(tmp_path), include="*.py")
    assert "foo.py" in out
    assert "bar.js" not in out


# ------------- edge cases -----------------------------------------------------
def test_binary_files_skipped(tmp_path: Path):
    make_file(tmp_path, "text.txt", b"match_me")
    make_file(tmp_path, "bin.bin", b"\x00\x01\x02match_me")  # binary marker

    out = GrepTool().run(pattern="match_me", path=str(tmp_path))
    assert "text.txt" in out
    assert "bin.bin" not in out  # binary should be ignored


def test_invalid_regex(tmp_path: Path):
    with pytest.raises(ToolError):
        GrepTool().run(pattern="(*)", path=str(tmp_path))


def test_path_not_directory(tmp_path: Path):
    file_path = make_file(tmp_path, "lonely.txt", b"hi")
    with pytest.raises(ToolError):
        GrepTool().run(pattern="hi", path=str(file_path))  # pass file path instead of dir


def test_result_truncation(tmp_path: Path):
    # Create more matches than MAX_RESULTS
    for i in range(MAX_RESULTS + 5):
        make_file(tmp_path, f"f{i}.txt", b"needle")

    out = GrepTool().run(pattern="needle", path=str(tmp_path))
    # header + MAX_RESULTS lines expected
    assert len(out.splitlines()) == MAX_RESULTS + 1
    assert "truncated" in out.lower()


def test_sorted_by_mtime(tmp_path: Path):
    # Newest file should appear first in results
    make_file(tmp_path, "old.txt", b"hit", mtime_shift=60)
    newest = make_file(tmp_path, "new.txt", b"hit", mtime_shift=5)

    out = GrepTool().run(pattern="hit", path=str(tmp_path))
    first_entry = out.splitlines()[1]  # line 0 is header
    first_path = first_entry.split(":", 1)[0]
    assert first_path == newest.relative_to(tmp_path).as_posix()


def test_excluded_dirs(tmp_path: Path):
    # Files inside build and virtual-env directories should be ignored
    (tmp_path / "build").mkdir()
    (tmp_path / "venv").mkdir()
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "build" / "hit.txt").write_text("needle")
    (tmp_path / "venv" / "hit.txt").write_text("needle")
    (tmp_path / "node_modules" / "hit.txt").write_text("needle")
    (tmp_path / "root.txt").write_text("needle")

    out = GrepTool().run(pattern="needle", path=str(tmp_path))
    # Only the root file should appear in the output
    assert "root.txt" in out
    assert "build/hit.txt" not in out
    assert "venv/hit.txt" not in out
    assert "node_modules/hit.txt" not in out
