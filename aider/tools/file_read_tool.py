"""
FileReadTool – read a text or image file from the local filesystem.

• For text: returns up-to 2 000 lines (2 000 chars each). Supports
  ``offset``/``limit`` so the model can page through large files.
• For images (.png .jpg .jpeg .gif .bmp .webp): returns a single
  ``data:image/<ext>;base64,....`` string.
• For Jupyter notebooks (.ipynb): refuses and instructs the model to
  call ``read_notebook`` instead.

Security:
  – ``file_path`` must be ABSOLUTE.  
  – path must lie within a directory that has read-permission
    (aider.permissions).  
  – directory traversal outside that sandbox is blocked.
"""
from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image  # pillow
from aider.permissions import has_read_permission
from aider.utils import is_image_file
from .base_tool import BaseTool, ToolError

# ---------------- constants ---------------------------------------------------
MAX_LINES_TO_READ = 2_000
MAX_LINE_LENGTH = 2_000
MAX_OUTPUT_SIZE = int(0.25 * 1024 * 1024)  # 256 kB text
MAX_IMAGE_BYTES = int(3.75 * 1024 * 1024)  # ~5 MB original → ~3.75 MB base64


class FileReadTool(BaseTool):
    # ------------- metadata ---------------------------------------------------
    name = "file_read"
    description = (
        "Read a local file (text or image). For .ipynb use the read_notebook tool."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file.",
            },
            "offset": {
                "type": "integer",
                "description": "Line number to start reading (1-based).",
                "minimum": 1,
            },
            "limit": {
                "type": "integer",
                "description": "Number of lines to read.",
                "minimum": 1,
            },
        },
        "required": ["file_path"],
        "additionalProperties": False,
    }

    # ------------- main entry point -------------------------------------------
    def run(
        self,
        *,
        file_path: str,
        offset: int | None = None,
        limit: int | None = None,
    ) -> str:
        path = Path(file_path).expanduser().resolve()
        self._validate_path(path)

        # Delegate notebooks
        if path.suffix.lower() == ".ipynb":
            raise ToolError("Use the `read_notebook` tool for .ipynb files.")

        # Image branch
        if is_image_file(path):
            return self._read_image(path)

        # Text branch
        return self._read_text(path, offset or 1, limit)

    # ------------- validation --------------------------------------------------
    @staticmethod
    def _validate_path(path: Path):
        if not path.is_absolute():
            raise ToolError("file_path must be ABSOLUTE")
        if not path.exists():
            raise ToolError(f"{path} does not exist")
        if not has_read_permission(path):
            raise ToolError(f"Read permission denied for {path}")

    # ------------- text helpers ------------------------------------------------
    @staticmethod
    def _line_iter(path: Path) -> tuple[List[str], int]:
        lines, total = [], 0
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                total += 1
                if len(raw) > MAX_LINE_LENGTH:
                    raw = raw[: MAX_LINE_LENGTH] + "…\n"
                lines.append(raw)
        return lines, total

    def _read_text(self, path: Path, offset: int, limit: int | None) -> str:
        lines, total = self._line_iter(path)

        if offset > total:
            raise ToolError("Offset beyond end of file")

        start = offset - 1
        end = start + (limit or MAX_LINES_TO_READ)
        chunk = lines[start:end]

        blob = "".join(chunk)
        if len(blob.encode()) > MAX_OUTPUT_SIZE and not limit:
            max_kb = MAX_OUTPUT_SIZE // 1024
            raise ToolError(
                f"File exceeds {max_kb} KB. Use offset/limit or grep specific content."
            )

        header = (
            f"{path} ({len(chunk)} lines, showing {offset}-{offset+len(chunk)-1} of {total})"
        )
        return header + "\n" + blob

    # ------------- image helpers ----------------------------------------------
    def _read_image(self, path: Path) -> str:
        if path.stat().st_size > MAX_IMAGE_BYTES:
            raise ToolError(
                f"Image larger than {MAX_IMAGE_BYTES//1024} KB; cannot embed."
            )
        payload = base64.b64encode(path.read_bytes()).decode()
        ext = path.suffix.lower().lstrip(".")
        return f"data:image/{ext};base64,{payload}"
