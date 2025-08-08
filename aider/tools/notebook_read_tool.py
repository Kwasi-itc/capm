"""
NotebookReadTool – extracts code/text cells (and basic outputs) from a
Jupyter notebook (.ipynb) file and returns them as plain text blocks.

Each cell is emitted as:

    <cell N>{optional-metadata}{source}</cell N>
    [outputs...]

Outputs are concatenated; images are replaced with ``[[image output]]``.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from aider.permissions import has_read_permission
from .base_tool import BaseTool, ToolError

MAX_CELLS = 500  # safety cap to avoid flooding the chat


class NotebookReadTool(BaseTool):
    # ---------- metadata advertised to the LLM --------------------------
    name = "read_notebook"
    description = (
        "Extract and read source code from all cells of a Jupyter notebook (.ipynb)."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "notebook_path": {
                "type": "string",
                "description": "Absolute path to the .ipynb file",
            }
        },
        "required": ["notebook_path"],
        "additionalProperties": False,
    }

    # ---------- helpers -------------------------------------------------
    @staticmethod
    def _output_text(output) -> str:
        """Convert a single output object into plain text (images → placeholder)."""
        otype = output.get("output_type")
        if otype == "stream":
            txt = output.get("text") or ""
            return "".join(txt) if isinstance(txt, list) else str(txt)
        if otype in {"execute_result", "display_data"}:
            data = output.get("data", {})
            if "text/plain" in data:
                return str(data["text/plain"])
            if "image/png" in data or "image/jpeg" in data:
                return "[[image output]]"
        if otype == "error":
            ename = output.get("ename")
            evalue = output.get("evalue")
            tb = "\n".join(output.get("traceback", []))
            return f"{ename}: {evalue}\n{tb}"
        return ""

    @classmethod
    def _cell_block(cls, idx: int, cell, language: str) -> str:
        """Render one notebook cell (plus outputs) to a string block."""
        cell_type = cell.get("cell_type", "code")
        source_raw = cell.get("source", [])
        source = "".join(source_raw) if isinstance(source_raw, list) else str(source_raw)

        meta = []
        if cell_type != "code":
            meta.append(f"<cell_type>{cell_type}</cell_type>")
        if cell_type == "code" and language and language != "python":
            meta.append(f"<language>{language}</language>")

        header = f"<cell {idx}>" + "".join(meta)
        footer = f"</cell {idx}>"

        block = f"{header}{source}{footer}"

        for out in cell.get("outputs", []):
            txt = cls._output_text(out)
            if txt:
                block += "\n" + txt.rstrip()

        return block

    # ---------- main entry point ---------------------------------------
    def run(self, *, notebook_path: str) -> str:
        if not os.path.isabs(notebook_path):
            raise ToolError("notebook_path must be an ABSOLUTE path")

        nb_path = Path(notebook_path).expanduser().resolve()
        if not nb_path.exists():
            raise ToolError(f"{nb_path} does not exist")
        if nb_path.suffix.lower() != ".ipynb":
            raise ToolError("File must have a .ipynb extension")
        if not has_read_permission(nb_path):
            raise ToolError(f"Read permission denied for {nb_path}")

        try:
            nb_json = json.loads(nb_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"Unable to parse {nb_path}: {exc}") from exc

        language = (
            nb_json.get("metadata", {})
            .get("language_info", {})
            .get("name", "python")
        )

        cells = nb_json.get("cells", [])
        if not cells:
            return "No cells found in notebook"

        blocks: List[str] = []
        for idx, cell in enumerate(cells):
            if idx >= MAX_CELLS:
                blocks.append("[[truncated: too many cells]]")
                break
            blocks.append(self._cell_block(idx, cell, language))

        return "\n".join(blocks)
