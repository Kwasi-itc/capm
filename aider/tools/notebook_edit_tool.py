"""
NotebookEditTool – replace / insert / delete a specific cell inside a
Jupyter notebook (.ipynb).

Edit-modes
    replace (default) – overwrite the cell source, optionally its type
    insert             – insert new cell at index
    delete             – delete cell at index

The notebook_path must be ABSOLUTE.  Write permission is enforced via
aider.permissions.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Literal

from aider.permissions import has_write_permission
from .base_tool import BaseTool, ToolError

EditMode = Literal["replace", "insert", "delete"]
MAX_CELLS = 500  # safeguard, same value used for read tool


class NotebookEditTool(BaseTool):
    # ------------------------------------------------------------------ #
    # metadata advertised to the LLM
    # ------------------------------------------------------------------ #
    name = "edit_notebook"
    description = "Replace / insert / delete a cell in a Jupyter notebook (.ipynb)."
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "notebook_path": {
                "type": "string",
                "description": "Absolute path to the .ipynb file",
            },
            "cell_number": {
                "type": "integer",
                "description": "0-based index of the cell to modify",
                "minimum": 0,
            },
            "new_source": {
                "type": "string",
                "description": "New source code / markdown for the cell",
            },
            "cell_type": {
                "type": "string",
                "enum": ["code", "markdown"],
                "description": (
                    "(optional) cell_type for insert or to change existing cell "
                    "when replacing"
                ),
            },
            "edit_mode": {
                "type": "string",
                "enum": ["replace", "insert", "delete"],
                "description": "replace | insert | delete   (default replace)",
            },
        },
        "required": ["notebook_path", "cell_number", "new_source"],
        "additionalProperties": False,
    }

    # ------------------------------------------------------------------ #
    # main entry point
    # ------------------------------------------------------------------ #
    def run(  # noqa: D401
        self,
        *,
        notebook_path: str,
        cell_number: int,
        new_source: str,
        cell_type: str | None = None,
        edit_mode: EditMode | None = None,
    ) -> str:
        # ----- validation ------------------------------------------------
        if not os.path.isabs(notebook_path):
            raise ToolError("notebook_path must be an ABSOLUTE path")
        nb_path = Path(notebook_path).expanduser().resolve()

        if not nb_path.exists():
            raise ToolError(f"{nb_path} does not exist")
        if nb_path.suffix.lower() != ".ipynb":
            raise ToolError("File must have .ipynb extension")
        if not has_write_permission(nb_path):
            raise ToolError(f"Write permission denied for {nb_path}")

        mode: EditMode = edit_mode or "replace"
        if mode == "insert" and cell_type is None:
            raise ToolError("cell_type is required when edit_mode=insert")

        # ----- load notebook --------------------------------------------
        try:
            nb_json = json.loads(nb_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"Unable to parse {nb_path}: {exc}") from exc

        cells = nb_json.get("cells", [])
        if len(cells) > MAX_CELLS:
            raise ToolError("Notebook too large for safe editing")

        if mode == "insert":
            if cell_number > len(cells):
                raise ToolError(
                    f"cell_number out of bounds for insert (max {len(cells)})"
                )
        elif cell_number >= len(cells):
            raise ToolError(
                f"cell_number out of bounds; notebook has {len(cells)} cells"
            )

        # ----- apply edit ----------------------------------------------
        if mode == "delete":
            cells.pop(cell_number)
            summary = f"Deleted cell {cell_number}"
        elif mode == "insert":
            new_cell = {
                "cell_type": cell_type,
                "source": new_source,
                "metadata": {},
            }
            if cell_type == "code":
                new_cell["outputs"] = []
            cells.insert(cell_number, new_cell)
            summary = f"Inserted cell {cell_number} with {len(new_source)} chars"
        else:  # replace
            target = cells[cell_number]
            target["source"] = new_source
            target["execution_count"] = None
            target["outputs"] = []
            if cell_type and cell_type != target.get("cell_type"):
                target["cell_type"] = cell_type
            summary = f"Updated cell {cell_number} with {len(new_source)} chars"

        # ----- save -----------------------------------------------------
        nb_path.write_text(
            json.dumps(nb_json, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
        return summary
