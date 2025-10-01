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

# Ensure the edit tool can verify that the file has been read
from .file_read_tool import _FILES_READ

from .base_tool import BaseTool, ToolError

MAX_DIFF_LINES = 200

# supported diff/edit output formats
_DEFAULT_EDIT_FORMAT = "unified"
_SUPPORTED_EDIT_FORMATS = {"unified", "whole", "edit-block"}


class FileEditTool(BaseTool):
    # --------------- metadata shown to the LLM --------------------
    name = "file_edit"
    description = (
        "Performs exact string replacements in files.\n\n"
        "Usage:\n"
        "- You must use your `Read` tool at least once in the conversation before editing. "
        "This tool will error if you attempt an edit without reading the file.\n"
        "- When editing text from Read tool output, ensure you preserve the exact indentation "
        "(tabs/spaces) as it appears AFTER the line number prefix. The line number prefix "
        "format is: spaces + line number + tab. Never include any part of the line number "
        "prefix in the old_string or new_string.\n"
        "- ALWAYS prefer editing existing files in the codebase. NEVER write new files unless "
        "explicitly required.\n"
        "- Only use emojis if the user explicitly requests it. Avoid adding emojis to files "
        "unless asked.\n"
        "- The edit will FAIL if `old_string` is not unique in the file. Either provide a larger "
        "string with more surrounding context to make it unique or set `replace_all` to true.\n"
        "- Use `replace_all` for renaming or replacing every instance of a string across the file."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The absolute path to the file to modify",
            },
            "old_string": {
                "type": "string",
                "description": "The text to replace",
            },
            "new_string": {
                "type": "string",
                "description": "The text to replace it with (must be different from old_string)",
            },
            "replace_all": {
                "type": "boolean",
                "default": False,
                "description": "Replace all occurences of old_string (default false)",
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
        file_path: str | None = None,
        old_string: str | None = None,
        new_string: str | None = None,
        replace_all: bool | None = None,
        edit_format: str | None = None,
        line_number: int | None = None,
        before_context: str | None = None,
        after_context: str | None = None,
        changes: list[dict[str, Any]] | None = None,
    ) -> str:
        start = time.time()
        replace_all = bool(replace_all)

        # -------- multi-file batch processing ---------------------
        if changes:
            results: list[str] = []
            for change in changes:
                single_result = self.run(**{**change, "edit_format": edit_format})
                results.append(single_result)
            return "\n\n".join(results)

        if file_path is None or old_string is None or new_string is None:
            raise ToolError("file_path, old_string and new_string must be provided.")

        target = Path(file_path).expanduser().resolve()

        # Enforce read-before-edit policy
        if str(target) not in _FILES_READ:
            raise ToolError(
                "You must use the Read tool on this file earlier in the conversation "
                "before attempting to edit it."
            )

        # -------- select diff/edit format ----------
        edit_format = (edit_format or _DEFAULT_EDIT_FORMAT).lower()
        if edit_format not in _SUPPORTED_EDIT_FORMATS:
            raise ToolError(
                f"Unsupported edit_format '{edit_format}'. "
                f"Allowed formats: {', '.join(sorted(_SUPPORTED_EDIT_FORMATS))}."
            )

        # -------- validate context requirement ------------
        # Heuristic: more context helps ensure the correct match, but don't hard-fail.
        # If too little context is provided we will later verify the match is unambiguous.

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

        # -------- direct substring replacement if possible --------
        substring_count = original.count(old_string)
        if substring_count:
            # Enforce uniqueness unless replace_all or explicit disambiguation provided
            if (
                substring_count > 1
                and not replace_all
                and not any([line_number, before_context, after_context])
            ):
                raise ToolError(
                    f"`old_string` occurs {substring_count} times. "
                    "Provide a more specific `old_string`, set `replace_all` to true, "
                    "or add `line_number`/`before_context`/`after_context` to disambiguate."
                )

            # Perform the replacement
            updated = (
                original.replace(old_string, new_string)
                if replace_all
                else original.replace(old_string, new_string, 1)
            )

            if updated == original:
                raise ToolError("Edit produced no change (strings identical).")

            self._write_text(target, updated)
            diff = self._make_output(original, updated, str(target), edit_format)
            ms = int((time.time() - start) * 1000)
            verb = "Deleted" if new_string == "" else "Updated"
            scope = "all occurrences of" if replace_all else "1 occurrence of"
            return f"{verb} {scope} '{old_string}' in {target} in {ms} ms\n{diff}"

        # -------- locate ALL occurrences --------------------------
        lines = original.splitlines(keepends=True)
        occurrences: list[int] = []
        for idx, line in enumerate(lines):
            if old_string in line:
                occurrences.append(idx)

        if not occurrences:
            # If the requested change already appears in the file, treat as idempotent-success
            if new_string and new_string in original:
                ms = int((time.time() - start) * 1000)
                return (
                    f"No edit needed for {target} (already contains the requested change) "
                    f"in {ms} ms"
                )

            # Provide a helpful hint by showing the most similar lines
            hint = ""
            try:
                sample_lines = [l.strip() for l in lines if l.strip()]
                close = difflib.get_close_matches(old_string.strip(), sample_lines, n=3, cutoff=0.5)
                if close:
                    joined = "\n  • ".join(close)
                    hint = f"\nDid you mean one of these lines?\n  • {joined}"
            except Exception:
                pass
            # Provide additional guidance on multi-line matches
            raise ToolError(
                "`old_string` not found in file. "
                "If you are matching multiple lines, double-check that:\n"
                "• The text matches *exactly* including spaces and tabs.\n"
                "• All newline characters (`\\n`) are in the correct places.\n"
                "• The file does not already contain an extra line you’re trying to insert.\n"
                f"{hint}"
            )

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
