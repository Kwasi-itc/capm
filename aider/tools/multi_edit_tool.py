"""
MultiEditTool – perform several exact find-and-replace operations on a single file
in one atomic action.

The tool enforces the same guarantees as FileEditTool while allowing an array
of edits to be applied sequentially.  Either every edit succeeds and the file
is written once, or the operation aborts with no changes.
"""
from __future__ import annotations

import difflib
import time
from pathlib import Path
from typing import Any, Dict, List

from .file_read_tool import _FILES_READ
from .file_edit_tool import FileEditTool
from .base_tool import BaseTool, ToolError, print_proposed_edits

# ---------------------------------------------------------------------------

class MultiEditTool(BaseTool):
    # ---------------- metadata visible to the LLM ---------------------------
    name = "MultiEdit"
    description = (
        "This is a tool for making multiple edits to a single file in one operation. "
        "It is built on top of the Edit tool and allows you to perform multiple "
        "find-and-replace operations efficiently. Prefer this tool over the Edit tool "
        "when you need to make multiple edits to the same file."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The absolute path to the file to modify",
            },
            "edits": {
                "type": "array",
                "minItems": 1,
                "description": (
                    "Array of edit operations to perform sequentially on the file"
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "old_string": {
                            "type": "string",
                            "description": "The text to replace",
                        },
                        "new_string": {
                            "type": "string",
                            "description": "The text to replace it with",
                        },
                        "replace_all": {
                            "type": "boolean",
                            "default": False,
                            "description": (
                                "Replace all occurrences of old_string (default false)."
                            ),
                        },
                    },
                    "required": ["old_string", "new_string"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["file_path", "edits"],
        "additionalProperties": False,
    }

    # ---------------- helpers ----------------------------------------------
    @staticmethod
    def _read_text(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text()

    @staticmethod
    def _write_text(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    # ---------------- main entry point -------------------------------------
    def run(
        self,
        *,
        file_path: str,
        edits: List[Dict[str, Any]],
    ) -> str:
        start = time.time()
        target = Path(file_path).expanduser().resolve()
        # Preview the edits with colored diff-style output
        print_proposed_edits({"file_path": str(target), "edits": edits})

        # ------------- read-before-edit enforcement -------------------------
        if str(target) not in _FILES_READ:
            raise ToolError(
                "You must use the Read tool on this file earlier in the conversation "
                "before attempting to edit it."
            )

        # ------------- file existence / creation ---------------------------
        creating_new_file = edits[0].get("old_string", "") == ""  # first edit may create file
        if creating_new_file:
            if target.exists():
                raise ToolError("Cannot create file: path already exists.")
            original = ""
        else:
            if not target.is_file():
                raise ToolError(f"Target path {target} does not exist or is not a file.")
            original = self._read_text(target)

        updated = original

        # ------------- apply edits sequentially ----------------------------
        for idx, edit in enumerate(edits, start=1):
            old = edit.get("old_string", "")
            new = edit.get("new_string", "")
            replace_all = bool(edit.get("replace_all", False))

            if old == "" and idx != 1:
                raise ToolError("Only the first edit may have empty old_string to create a file.")
            if old == new:
                raise ToolError(f"Edit {idx}: old_string and new_string are identical.")

            if old == "":
                # file creation already handled
                updated = new
                continue

            occurrence_count = updated.count(old)
            if occurrence_count == 0:
                raise ToolError(f"Edit {idx}: `old_string` not found in file.")
            if occurrence_count > 1 and not replace_all:
                raise ToolError(
                    f"Edit {idx}: `old_string` occurs {occurrence_count} times. "
                    "Provide a more specific `old_string` or set replace_all to true."
                )

            updated = (
                updated.replace(old, new) if replace_all else updated.replace(old, new, 1)
            )

        if updated == original:
            raise ToolError("All edits produced no change (strings identical).")

        # ------------- write & diff ----------------------------------------
        self._write_text(target, updated)
        diff = FileEditTool._make_output(original, updated, str(target), "unified")
        ms = int((time.time() - start) * 1000)
        return f"Applied {len(edits)} edits to {target} in {ms} ms\n{diff}"
