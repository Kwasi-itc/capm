from pathlib import Path
import os

import pytest

from aider.permissions import (
    clear_permissions,
    grant_read,
    grant_write,
    has_read_permission,
    has_write_permission,
    path_in_original_cwd,
)

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def make_tmp_dir(tmp_path: Path, name: str) -> Path:
    d = tmp_path / name
    d.mkdir()
    return d


# --------------------------------------------------------------------------- #
# tests
# --------------------------------------------------------------------------- #
def test_permissions_basics(tmp_path: Path):
    clear_permissions()

    some_dir = make_tmp_dir(tmp_path, "data")

    assert not has_read_permission(some_dir)
    assert not has_write_permission(some_dir)

    grant_read(some_dir)
    assert has_read_permission(some_dir)
    assert not has_write_permission(some_dir)

    grant_write(some_dir)
    assert has_write_permission(some_dir)


def test_prefix_grant(tmp_path: Path):
    clear_permissions()

    parent = make_tmp_dir(tmp_path, "parent")
    child = parent / "child"
    child.mkdir()

    grant_read(parent)
    assert has_read_permission(child)  # child inherits parent grant

    # but reverse is not true
    clear_permissions()
    grant_read(child)
    assert not has_read_permission(parent)


def test_path_in_original_cwd(tmp_path: Path):
    # Original CWD is process start dir; tmp_path should be elsewhere.
    # The helper should therefore return False.
    assert not path_in_original_cwd(tmp_path)
