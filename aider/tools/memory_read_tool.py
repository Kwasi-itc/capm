"""
MemoryReadTool – read text from Aider’s *memory directory*.

If ``file_path`` (relative) is supplied, the tool returns that file’s content.
Otherwise it returns the root ``index.md`` (if present) and a list of all files
stored under the memory directory.

Security: it refuses to access paths that would escape the sandbox.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from .base_tool import BaseTool, ToolError
from .memory_write_tool import MEMORY_DIR  # reuse constant


class MemoryReadTool(BaseTool):
    # ---------------- metadata for the LLM -------------------------
    name = "memory_read"
    description = "Read the content of a memory file or, if omitted, the memory index + file list."
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Optional relative path (inside memory dir) to read",
            }
        },
        "required": [],
        "additionalProperties": False,
    }

    # ---------------- helpers --------------------------------------
    @staticmethod
    def _secure_resolve(rel_path: str) -> Path:
        dest = (MEMORY_DIR / rel_path).expanduser().resolve()
        if not str(dest).startswith(str(MEMORY_DIR)):
            raise ToolError("Invalid memory file path – must stay within MEMORY_DIR")
        return dest

    @staticmethod
    def _list_files() -> List[str]:
        return sorted(f"- {p}" for p in MEMORY_DIR.rglob("*") if p.is_file())

    # ---------------- main execution -------------------------------
    def run(self, *, file_path: str | None = None) -> str:  # noqa: D401
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)

        if file_path:
            target = self._secure_resolve(file_path)
            if not target.exists():
                raise ToolError("Memory file does not exist")
            return target.read_text(encoding="utf-8")

        # default: index + listing
        index_path = MEMORY_DIR / "index.md"
        index_content = index_path.read_text(encoding="utf-8") if index_path.exists() else ""

        listing = "\n".join(self._list_files()) or "(no memory files)"
        quotes = "'''"
        return (
            f"Here are the contents of the root memory file, `{index_path}`:\n"
            f"{quotes}\n{index_content}\n{quotes}\n\n"
            f"Files in the memory directory:\n{listing}"
        )
