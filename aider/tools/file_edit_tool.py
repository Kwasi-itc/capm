"""
FileEditTool – create / update / delete ONE uniquely-identified block of text.

Usage rules
-----------
• old_string == ""    → create new file whose contents are new_string
• new_string == ""    → delete the single occurrence of old_string
• otherwise           → replace the single occurrence of old_string with new_string

The tool writes the file and returns a unified diff (truncated) so the assistant
can show the changes to the user.

This follows the same contract/structure used by GlobTool and GrepTool.
"""
from __future__ import annotations

import difflib
import time
from pathlib import Path
from typing import Any, Dict

from .base_tool import BaseTool, ToolError

MAX_DIFF_LINES = 200

# supported diff/edit output formats
_DEFAULT_EDIT_FORMAT = "unified"
_SUPPORTED_EDIT_FORMATS = {"unified", "whole", "edit-block"}


class FileEditTool(BaseTool):
    # --------------- metadata shown to the LLM --------------------
    name = "file_edit"
    description = (
        "Create, update or delete the contents of a file by replacing ONE unique "
        "`old_string` with `new_string`. If `old_string` is empty a new file is "
        "created. If `new_string` is empty the matching text is deleted."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path of the file to modify (absolute preferred)",
            },
            "old_string": {
                "type": "string",
                "description": (
                    "Exact literal text to replace. "
                    "Must include at least 3 complete lines *before* and *after* the target "
                    "code so the match is unique. "
                    "Leave empty to create a new file."
                ),
            },
            "new_string": {
                "type": "string",
                "description": "Replacement text. Leave empty to delete the match.",
            },
            "edit_format": {
                "type": "string",
                "description": "Optional format of the diff to return. "
                "One of 'unified', 'whole', or 'edit-block'. Defaults to 'unified'.",
                "enum": ["unified", "whole", "edit-block"],
            },
            "line_number": {
                "type": "integer",
                "description": "1-based line number where `old_string` should be replaced if "
                "there are multiple occurrences.",
            },
            "before_context": {
                "type": "string",
                "description": "Text expected on the line *before* `old_string` to help "
                "uniquely identify the correct match.",
            },
            "after_context": {
                "type": "string",
                "description": "Text expected on the line *after* `old_string` to help "
                "uniquely identify the correct match.",
            },
        },
        "required": ["file_path", "old_string", "new_string"],
        "additionalProperties": False,
    }

    # ---------------- helpers -------------------------------------
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

    # -------- additional diff format helpers ---------------------
    @staticmethod
    def _make_whole(updated: str, rel_name: str) -> str:
        """
        Return the full updated file as the diff payload.
        """
        return f"----- {rel_name} (whole file) -----\n{updated}"

    @staticmethod
    def _make_edit_block(orig: str, updated: str, rel_name: str) -> str:
        """
        Produce a minimal edit-block style diff showing only the changed lines
        with no surrounding context. This format is easier for the LLM to
        apply as a targeted patch.
        """
        diff_lines = list(
            difflib.unified_diff(
                orig.splitlines(keepends=True),
                updated.splitlines(keepends=True),
                fromfile=rel_name,
                tofile=rel_name,
                n=0,  # no context lines
            )
        )[2:]  # drop the ---/+++ headers
        if len(diff_lines) > MAX_DIFF_LINES:
            diff_lines = diff_lines[:MAX_DIFF_LINES] + ["\n... (diff truncated) ...\n"]
        return "".join(diff_lines)

    @staticmethod
    def _make_output(orig: str, updated: str, rel_name: str, edit_format: str) -> str:
        if edit_format == "unified":
            return FileEditTool._make_diff(orig, updated, rel_name)
        if edit_format == "whole":
            return FileEditTool._make_whole(updated, rel_name)
        # default to edit-block
        return FileEditTool._make_edit_block(orig, updated, rel_name)

    # ---------------- main entry point ----------------------------
    def run(
        self,
        *,
        file_path: str,
        old_string: str,
        new_string: str,
        edit_format: str | None = None,
        line_number: int | None = None,
        before_context: str | None = None,
        after_context: str | None = None,
    ) -> str:
        start = time.time()
        target = Path(file_path).expanduser().resolve()

        # -------- select diff/edit format ----------
        edit_format = (edit_format or _DEFAULT_EDIT_FORMAT).lower()
        if edit_format not in _SUPPORTED_EDIT_FORMATS:
            raise ToolError(
                f"Unsupported edit_format '{edit_format}'. "
                f"Allowed formats: {', '.join(sorted(_SUPPORTED_EDIT_FORMATS))}."
            )

        # -------- validate context requirement ------------
        if old_string:
            # Require at least 3 lines of context *before* and *after* the target line
            line_breaks = old_string.count("\n")
            if line_breaks < 6:
                raise ToolError(
                    "old_string must include at least 3 lines *before* and 3 lines *after* "
                    "the target text (≥ 6 newline characters)."
                )

        # -------- create new file --------
        if old_string == "":
            if target.exists():
                raise ToolError("Cannot create file: path already exists.")
            self._write_text(target, new_string)
            diff = self._make_output("", new_string, str(target), edit_format)
            ms = int((time.time() - start) * 1000)
            return f"Created {target} in {ms} ms\n{diff}"

        # -------- update or delete -------
        if not target.is_file():
            raise ToolError(f"Target path {target} does not exist or is not a file.")

        original = self._read_text(target)

        # -------- locate ALL occurrences --------------------------
        lines = original.splitlines(keepends=True)
        occurrences: list[int] = []
        for idx, line in enumerate(lines):
            if old_string in line:
                occurrences.append(idx)

        if not occurrences:
            raise ToolError("`old_string` not found in file.")

        # -------- disambiguate occurrences ------------------------
        selected_idx: int | None = None

        if line_number is not None:
            # 1-based external line numbers
            for idx in occurrences:
                if idx + 1 == line_number:
                    selected_idx = idx
                    break
            if selected_idx is None:
                raise ToolError(f"`old_string` not found at line {line_number}.")

        elif before_context is not None or after_context is not None:
            for idx in occurrences:
                ok = True
                if before_context is not None and idx > 0:
                    ok &= before_context in lines[idx - 1]
                if after_context is not None and idx < len(lines) - 1:
                    ok &= after_context in lines[idx + 1]
                if ok:
                    if selected_idx is not None:
                        raise ToolError(
                            "Provided context matches multiple occurrences; "
                            "please add more specific context."
                        )
                    selected_idx = idx
            if selected_idx is None:
                raise ToolError("No occurrence matches the provided context.")

        else:
            if len(occurrences) > 1:
                raise ToolError(
                    f"`old_string` occurs {len(occurrences)} times. Provide "
                    "`line_number`, `before_context`, or `after_context` to disambiguate."
                )
            selected_idx = occurrences[0]

        # -------- perform the single replacement ------------------
        lines[selected_idx] = lines[selected_idx].replace(old_string, new_string, 1)
        updated = "".join(lines)
        if updated == original:
            raise ToolError("Edit produced no change (strings identical).")

        self._write_text(target, updated)
        diff = self._make_output(original, updated, str(target), edit_format)
        ms = int((time.time() - start) * 1000)
        verb = "Deleted" if new_string == "" else "Updated"
        return f"{verb} {target} in {ms} ms\n{diff}"
