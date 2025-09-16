"""
GrepTool – a fast regex-based content search tool for Aider.

It scans files under a directory (defaults to CWD), returning the paths of files
whose *contents* match a regular-expression pattern.  Results are sorted by
modification time (newest first).  Designed to be used as an LLM “tool /
function”.
"""
from __future__ import annotations

import os
import re
import time
import mmap
from pathlib import Path
from typing import Any, Dict, List

from .base_tool import BaseTool, ToolError

MAX_RESULTS = 100

# Directories that are completely ignored during the search.
# This includes common build artefacts and dependency/virtual-env folders
# across many languages.
EXCLUDE_DIRS = {
    "build",
    "dist",
    "out",
    "target",
    "node_modules",
    "venv",
    ".venv",
}


class GrepTool(BaseTool):
    # -------- metadata sent to the LLM ---------------------------------
    name = "grep"
    description = (
        "Search file contents using a regular-expression pattern. "
        "If the pattern is not valid regex an error is raised. "
        "Returns matching file paths together with the first matching line and its "
        "line number (sorted by modification time). "
        "Common build, dependency and virtual-environment directories "
        "(e.g. node_modules, dist, target, venv) are automatically excluded."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Regular-expression pattern to search for",
            },
            "path": {
                "type": "string",
                "description": "Directory to search (defaults to current working directory)",
            },
            "include": {
                "type": "string",
                "description": 'Glob filter for files to include (e.g. "*.py" or "*.{ts,tsx}")',
            },
        },
        "required": ["pattern"],
        "additionalProperties": False,
    }

    # -------- helpers ---------------------------------------------------
    @staticmethod
    def _iter_files(root: Path, include_glob: str | None) -> List[Path]:
        """Yield Path objects under root matching the glob (or all files if glob is None)."""
        paths = root.rglob(include_glob) if include_glob else root.rglob("*")
        for p in paths:
            # Skip any paths that contain an excluded directory component
            if any(part in EXCLUDE_DIRS for part in p.parts):
                continue
            yield p

    # -------- main execution --------------------------------------------
    def run(self, *, pattern: str, path: str | None = None, include: str | None = None) -> str:
        """
        Search for ``pattern`` (regex) inside files under ``path`` (or CWD).

        Uses mmap for efficient binary scanning.  Each matching result is formatted as

            ``<relative_path>:<line_number>: <first_matching_line>``

        Results are '\n'-separated and sorted by newest-first file mtime.
        """
        try:
            # Compile both byte-level and str-level regexes
            bytes_regex = re.compile(pattern.encode("utf-8"))
            str_regex = re.compile(pattern)
        except re.error as e:
            raise ToolError(f"Invalid regular-expression pattern: {pattern!r} ({e})")

        root = Path(path or os.getcwd()).expanduser().resolve()
        if not root.is_dir():
            raise ToolError(f"Search path {root} is not a directory")

        start = time.time()
        matches: list[tuple[str, float, int, str]] = []  # (rel_path, mtime, line_no, line_text)

        for file_path in self._iter_files(root, include):
            if not file_path.is_file():
                continue

            try:
                file_stat = file_path.stat()
                if file_stat.st_size == 0:
                    continue

                with open(file_path, "rb") as f:
                    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                        # Skip likely binary files quickly
                        if mm.find(b"\0", 0, 1024) != -1:
                            continue
                        if bytes_regex.search(mm):
                            # Find first matching line (text mode)
                            line_no = 0
                            first_line = ""
                            try:
                                with open(file_path, "r", encoding="utf-8", errors="ignore") as txt_f:
                                    for i, line in enumerate(txt_f, 1):
                                        if str_regex.search(line):
                                            line_no = i
                                            first_line = line
                                            break
                            except OSError:
                                pass

                            rel_path = str(file_path.relative_to(root))
                            matches.append((rel_path, file_stat.st_mtime, line_no, first_line))
            except (ValueError, OSError):
                # Ignore unreadable or special files
                continue

        # Newest-first
        matches.sort(key=lambda item: item[1], reverse=True)

        duration_ms = int((time.time() - start) * 1000)
        num_files = len(matches)
        summary_lines = [
            f"{p}:{ln}: {lt.strip()}" for p, _, ln, lt in matches[:MAX_RESULTS]
        ]

        header = f"Found {num_files} file{'s' if num_files != 1 else ''} in {duration_ms}ms"
        if num_files > MAX_RESULTS:
            header += " (Results are truncated. Consider using a more specific path or pattern.)"

        summary = header + ("\n" + "\n".join(summary_lines) if summary_lines else "")
        return summary
