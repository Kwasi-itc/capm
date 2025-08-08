"""
MemoryWriteTool – persist arbitrary text inside Aider’s *memory directory*.

The destination is always resolved relative to MEMORY_DIR, preventing
path-traversal so the LLM can’t overwrite files outside that sandbox.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from .base_tool import BaseTool, ToolError

# Directory where memories are stored; user can override via env-var
MEMORY_DIR = Path(os.getenv("AIDER_MEMORY_DIR", "~/.aider_memory")).expanduser().resolve()


class MemoryWriteTool(BaseTool):
    # ------------------- metadata shown to the LLM --------------------
    name = "memory_write"
    description = "Write text content to a file inside Aider’s memory directory."
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Relative path (within the memory directory) to write.",
            },
            "content": {
                "type": "string",
                "description": "Text content to store in the file.",
            },
        },
        "required": ["file_path", "content"],
        "additionalProperties": False,
    }

    # ------------------- main execution ------------------------------
    def run(self, *, file_path: str, content: str) -> str:  # noqa: D401
        # Normalise & secure destination path
        dest = (MEMORY_DIR / file_path).expanduser().resolve()

        # Prevent directory traversal outside MEMORY_DIR
        if not str(dest).startswith(str(MEMORY_DIR)):
            raise ToolError("Invalid memory file path – must stay within MEMORY_DIR")

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
        except OSError as exc:
            raise ToolError(f"Unable to write memory file: {exc}") from exc

        return "Saved"
