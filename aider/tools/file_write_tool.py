"""
FileWriteTool – create or overwrite a file on the local filesystem.

Safety rules
• ``file_path`` must be ABSOLUTE.
• The destination path (or its parent) must have been granted write-permission
  via aider.permissions.
• Parent directories are created automatically.
• Returns a short confirmation string for the assistant.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from aider.permissions import has_write_permission
from .base_tool import BaseTool, ToolError

ENCODING = "utf-8"


class FileWriteTool(BaseTool):
    # -------- metadata advertised to the LLM -----------------------------
    name = "file_write"
    description = "Create or replace a text file on the local filesystem."
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the target file",
            },
            "content": {
                "type": "string",
                "description": "Exact text to write into the file",
            },
        },
        "required": ["file_path", "content"],
        "additionalProperties": False,
    }

    # -------- execution --------------------------------------------------
    def run(self, *, file_path: str, content: str) -> str:  # noqa: D401
        path = Path(file_path).expanduser().resolve()

        # validation
        if not path.is_absolute():
            raise ToolError("file_path must be ABSOLUTE")
        if not has_write_permission(path):
            raise ToolError(f"Write permission denied for {path}")

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            existed = path.exists()
            path.write_text(content, encoding=ENCODING)
        except OSError as exc:
            raise ToolError(f"Unable to write file: {exc}") from exc

        if existed:
            return f"Updated file {path}"
        return f"File created successfully at: {path}"
