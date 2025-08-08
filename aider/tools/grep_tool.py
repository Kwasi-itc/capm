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


class GrepTool(BaseTool):
    # -------- metadata sent to the LLM ---------------------------------
    name = "grep"
    description = (
        "Search file contents using a regular-expression pattern. "
        "Returns matching file paths (sorted by modification time)."
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
        if include_glob:
            yield from root.rglob(include_glob)
        else:
            yield from root.rglob("*")

    # -------- main execution --------------------------------------------
    def run(self, *, pattern: str, path: str | None = None, include: str | None = None) -> str:
        """
        Search for ``pattern`` (regex) inside files under ``path`` (or CWD).
        Uses mmap for efficient binary scanning.  Results are returned as a
        '\n'-separated list of relative paths sorted by newest-first mtime.
        """
        try:
            # Compile as bytes because mmap yields bytes
            regex = re.compile(pattern.encode("utf-8"))
        except re.error as exc:  # noqa: PERF203
            raise ToolError(f"Invalid regular expression: {exc}") from exc

        root = Path(path or os.getcwd()).expanduser().resolve()
        if not root.is_dir():
            raise ToolError(f"Search path {root} is not a directory")

        start = time.time()
        matches: list[tuple[str, float]] = []  # (relative_path, mtime)

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
                        if regex.search(mm):
                            rel_path = str(file_path.relative_to(root))
                            matches.append((rel_path, file_stat.st_mtime))
            except (ValueError, OSError):
                # Ignore unreadable or special files
                continue

        # Newest-first
        matches.sort(key=lambda item: item[1], reverse=True)
        sorted_paths = [p for p, _ in matches]

        duration_ms = int((time.time() - start) * 1000)
        num_files = len(sorted_paths)
        summary_lines = sorted_paths[:MAX_RESULTS]

        header = f"Found {num_files} file{'s' if num_files != 1 else ''} in {duration_ms}ms"
        if num_files > MAX_RESULTS:
            header += " (Results are truncated. Consider using a more specific path or pattern.)"

        summary = header + ("\n" + "\n".join(summary_lines) if summary_lines else "")
        return summary
