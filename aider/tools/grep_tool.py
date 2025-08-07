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
        try:
            regex = re.compile(pattern)
        except re.error as exc:  # noqa: PERF203
            raise ToolError(f"Invalid regular expression: {exc}") from exc

        root = Path(path or os.getcwd()).expanduser().resolve()
        if not root.is_dir():
            raise ToolError(f"Search path {root} is not a directory")

        start = time.time()
        matches: list[str] = []

        for file_path in self._iter_files(root, include):
            if not file_path.is_file():
                continue

            # Quick binary check
            try:
                with open(file_path, "rb") as fh:
                    if b"\0" in fh.read(1024):
                        continue
            except Exception:
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                    if regex.search(fh.read()):
                        matches.append(str(file_path.relative_to(root)))
            except Exception:
                continue

        # Sort by modification time (newest first) – stable tie-break by name
        matches.sort(
            key=lambda p: (-(root / p).stat().st_mtime),  # type: ignore[arg-type]
        )

        duration_ms = int((time.time() - start) * 1000)
        num_files = len(matches)

        summary_lines = matches[:MAX_RESULTS]
        summary = (
            f"Found {num_files} file{'s' if num_files != 1 else ''}\n" + "\n".join(summary_lines)
        )
        if num_files > MAX_RESULTS:
            summary += (
                "\n(Results are truncated. Consider using a more specific path or pattern.)"
            )

        # Optionally you could return structured data; for now we return the assistant-ready string
        return summary
