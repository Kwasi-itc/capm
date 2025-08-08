"""
GlobTool – fast filename pattern search for Aider.

Given a glob pattern such as ``*.py`` or ``src/**/*.ts`` it returns paths of
matching regular files under ``path`` (defaults to CWD), ordered by newest
modification time.  Output is a plain string suitable for the chat.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .base_tool import BaseTool, ToolError

MAX_RESULTS = 100


class GlobTool(BaseTool):
    # --------------- metadata advertised to the LLM ------------------
    name = "glob"
    description = (
        "Search filenames using a glob pattern (eg **/*.js or src/**/*.ts). "
        "Returns matching paths sorted by modification time."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Glob pattern used to match file paths",
            },
            "path": {
                "type": "string",
                "description": "Directory to search (defaults to current working directory)",
            },
        },
        "required": ["pattern"],
        "additionalProperties": False,
    }

    # ----------------- helpers ---------------------------------------
    @staticmethod
    def _collect_matches(root: Path, pattern: str) -> List[Tuple[str, float]]:
        """Return list of (relative_path, mtime) tuples matching the glob."""
        matches: List[Tuple[str, float]] = []
        for file_path in root.rglob(pattern):
            if not file_path.is_file():
                continue
            try:
                stat = file_path.stat()
            except OSError:
                continue
            rel_path = str(file_path.relative_to(root))
            matches.append((rel_path, stat.st_mtime))
        # newest first
        matches.sort(key=lambda item: item[1], reverse=True)
        return matches

    # ----------------- main entry point ------------------------------
    def run(self, *, pattern: str, path: str | None = None) -> str:
        root = Path(path or os.getcwd()).expanduser().resolve()
        if not root.is_dir():
            raise ToolError(f"Search path {root} is not a directory")

        start = time.time()
        matches = self._collect_matches(root, pattern)
        duration_ms = int((time.time() - start) * 1000)

        paths_only = [p for p, _ in matches]
        num_files = len(paths_only)

        header = f"Found {num_files} file{'s' if num_files != 1 else ''} in {duration_ms}ms"
        if num_files > MAX_RESULTS:
            header += " (Results are truncated. Consider using a more specific path or pattern.)"

        body = "\n".join(paths_only[:MAX_RESULTS])
        return header + ("\n" + body if body else "")
