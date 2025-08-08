"""
Simple in-memory filesystem permission helper for Aider.

It mirrors the behaviour of the TypeScript utility shown by the user:
the current Python process keeps two `set()` objects that contain the
**absolute directory prefixes** that are allowed for reading and writing.

Nothing in the existing codebase depends on this helper yet; tools or
other components may import and use the `has_read_permission()` /
`grant_read()` functions to enforce user-confirmed filesystem access.

The helper intentionally **does not** persist any state on disk: every
new Aider session starts with empty permission sets.
"""
from __future__ import annotations

import os
from pathlib import Path

# --------------------------------------------------------------------------- #
# internal storage
# --------------------------------------------------------------------------- #
_read_allowed: set[str] = set()
_write_allowed: set[str] = set()

# Store the process start directory as the “original cwd”
_ORIGINAL_CWD = Path(os.getcwd()).expanduser().resolve()


# --------------------------------------------------------------------------- #
# normalisation helpers
# --------------------------------------------------------------------------- #
def _to_abs(path: str | os.PathLike) -> str:
    """Return an absolute, normalised, *string* path."""
    return str(Path(path).expanduser().resolve())


# --------------------------------------------------------------------------- #
# query helpers
# --------------------------------------------------------------------------- #
def has_read_permission(directory: str | os.PathLike) -> bool:
    """Return True if *directory* is within any granted read prefix."""
    p = _to_abs(directory)
    return any(p.startswith(prefix) for prefix in _read_allowed)


def has_write_permission(directory: str | os.PathLike) -> bool:
    """Return True if *directory* is within any granted write prefix."""
    p = _to_abs(directory)
    return any(p.startswith(prefix) for prefix in _write_allowed)


# --------------------------------------------------------------------------- #
# grant helpers
# --------------------------------------------------------------------------- #
def _grant(dir_set: set[str], directory: str | os.PathLike):
    abs_dir = _to_abs(directory)

    # Remove redundant sub-paths that are already covered by the new prefix
    for existing in list(dir_set):
        if existing.startswith(abs_dir):
            dir_set.discard(existing)

    dir_set.add(abs_dir)


def grant_read(directory: str | os.PathLike):
    """Allow reading *directory* and all its sub-directories in this session."""
    _grant(_read_allowed, directory)


def grant_write(directory: str | os.PathLike):
    """Allow writing to *directory* and all its sub-directories in this session."""
    _grant(_write_allowed, directory)


def grant_read_original_dir():
    """Convenience: grant read permission for the directory where Aider started."""
    grant_read(_ORIGINAL_CWD)


def grant_write_original_dir():
    """Convenience: grant write permission for the directory where Aider started."""
    grant_write(_ORIGINAL_CWD)


# --------------------------------------------------------------------------- #
# utilities (mainly for tests)
# --------------------------------------------------------------------------- #
def clear_permissions():
    """Remove all previously granted permissions (read and write)."""
    _read_allowed.clear()
    _write_allowed.clear()


def path_in_original_cwd(path: str | os.PathLike) -> bool:
    """Return True if *path* is inside the process’ original cwd."""
    return _to_abs(path).startswith(str(_ORIGINAL_CWD))
