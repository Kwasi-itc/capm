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
import difflib
import time

from aider.permissions import has_write_permission
from .base_tool import BaseTool, ToolError

ENCODING = "utf-8"
MAX_DIFF_LINES = 200


class FileWriteTool(BaseTool):

    # ---------------- helpers -------------------------------------
    @staticmethod
    def _make_diff(orig: str, updated: str, rel_name: str) -> str:
        diff = list(
            difflib.unified_diff(
                orig.splitlines(keepends=True),
                updated.splitlines(keepends=True),
                fromfile=rel_name,
                tofile=rel_name,
                n=3,
            )
        )
        if len(diff) > MAX_DIFF_LINES:
            diff = diff[:MAX_DIFF_LINES] + ["\n... (diff truncated) ...\n"]
        return "".join(diff)
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
        start = time.time()
        path = Path(file_path).expanduser().resolve()

        # validation
        if not path.is_absolute():
            raise ToolError("file_path must be ABSOLUTE")
        if not has_write_permission(path):
            raise ToolError(f"Write permission denied for {path}")

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            existed = path.exists()
            original = path.read_text(encoding=ENCODING) if existed else ""
            path.write_text(content, encoding=ENCODING)
        except OSError as exc:
            raise ToolError(f"Unable to write file: {exc}") from exc

        diff = self._make_diff(original, content, str(path))
        ms = int((time.time() - start) * 1000)

        if existed:
            return f"Updated {path} in {ms} ms\n{diff}"
        return f"Created {path} in {ms} ms\n{diff}"
