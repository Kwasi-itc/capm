"""
LsTool – list files & directories beneath an *absolute* path.

Honours in-memory read permissions (`aider.permissions`).  
Refuses to operate if the caller hasn’t granted read access.
"""
from __future__ import annotations

import os
from collections import deque
from pathlib import Path
from typing import Any, Dict, List

from .base_tool import BaseTool, ToolError

MAX_FILES = 1_000
TRUNCATED_MSG = (
    f"There are more than {MAX_FILES} files in the repository. "
    "Use more specific tools (glob / grep / bash) to explore nested directories. "
    f"The first {MAX_FILES} entries are listed below:\n\n"
)


class LsTool(BaseTool):
    # ---------------- metadata shown to the LLM -------------------
    name = "ls"
    description = (
        "Recursively list files & directories for an ABSOLUTE path. "
        "Prefer the glob / grep tools when you already know patterns."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute directory path to list",
            }
        },
        "required": ["path"],
        "additionalProperties": False,
    }

    # ---------------- helper methods ------------------------------
    @staticmethod
    def _skip(p: Path) -> bool:
        """Skip hidden files and __pycache__ directories."""
        if p.name.startswith(".") and p.name != ".":
            return True
        if "__pycache__" in p.parts:
            return True
        return False

    @staticmethod
    def _breadth_first(root: Path) -> tuple[List[str], bool]:
        """
        Return (*relative* paths list, truncated?) breadth-first.
        Each directory path ends with '/'.

        The `truncated` flag becomes True if the directory tree contained
        more than ``MAX_FILES`` items and the listing was cut short.
        """
        rel_paths: List[str] = []
        q: deque[Path] = deque([root])
        truncated = False

        while q:
            cur = q.popleft()

            # skip printing the root directory itself
            if cur is not root:
                rel = cur.relative_to(root).as_posix()
                rel_paths.append(f"{rel}/" if cur.is_dir() else rel)

            if len(rel_paths) >= MAX_FILES:
                truncated = True
                break

            if cur.is_dir():
                try:
                    kids = sorted(cur.iterdir(), key=lambda p: p.name.lower())
                except (PermissionError, FileNotFoundError, OSError):
                    continue
                for kid in kids:
                    if LsTool._skip(kid):
                        continue
                    q.append(kid)

        return rel_paths, truncated

    @staticmethod
    def _paths_to_tree(paths: List[str]) -> Dict:
        """Convert list of paths to a nested-dict directory tree."""
        root: Dict[str, Dict] = {}
        for path in paths:
            parts = [part for part in path.split("/") if part]
            node = root
            for i, part in enumerate(parts):
                is_last = i == len(parts) - 1
                node = node.setdefault(
                    part, {} if not is_last or path.endswith("/") else None
                )
        return root

    @staticmethod
    def _print_tree(tree: Dict, prefix: str = "") -> str:
        lines: List[str] = []
        for name in sorted(tree):
            subtree = tree[name]
            lines.append(f"{prefix}- {name}{'/' if subtree is not None else ''}")
            if subtree:
                lines.append(LsTool._print_tree(subtree, prefix + '  '))
        return "\n".join(lines)

    # ---------------- main entry point ----------------------------
    def run(self, *, path: str) -> str:
        if not os.path.isabs(path):
            raise ToolError("The path argument must be ABSOLUTE, not relative")

        root = Path(path).expanduser().resolve()
        if not root.exists():
            raise ToolError(f"{root} does not exist")
        if not root.is_dir():
            raise ToolError(f"{root} is not a directory")

        rel_paths, truncated = self._breadth_first(root)
        tree_str = f"- {root}/\n" + self._print_tree(self._paths_to_tree(rel_paths))

        if truncated:
            return TRUNCATED_MSG + tree_str
        return tree_str
