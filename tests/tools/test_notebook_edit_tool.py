import json
from pathlib import Path

import pytest

from aider.permissions import clear_permissions, grant_write
from aider.tools.notebook_edit_tool import NotebookEditTool
from aider.tools.base_tool import ToolError


# ---------------- helpers ----------------------------------------------------
def make_nb(tmp: Path, name: str, cells):
    nb = {
        "cells": cells,
        "metadata": {"language_info": {"name": "python"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    p = tmp / name
    p.write_text(json.dumps(nb))
    return p


def read_nb(path: Path):
    return json.loads(path.read_text())


def setup_notebook(tmp_path: Path):
    cells = [
        {"cell_type": "markdown", "source": "# md\n"},
        {"cell_type": "code", "source": "print(1)\n", "outputs": []},
    ]
    return make_nb(tmp_path, "demo.ipynb", cells)


# ---------------- tests ------------------------------------------------------
def test_replace(tmp_path: Path):
    clear_permissions()
    nb = setup_notebook(tmp_path)
    grant_write(tmp_path)

    out = NotebookEditTool().run(
        notebook_path=str(nb),
        cell_number=1,
        new_source="print(2)\n",
        edit_mode="replace",
    )
    assert "Updated cell 1" in out
    data = read_nb(nb)
    assert data["cells"][1]["source"] == "print(2)\n"
    assert data["cells"][1]["outputs"] == []


def test_insert(tmp_path: Path):
    clear_permissions()
    nb = setup_notebook(tmp_path)
    grant_write(tmp_path)

    NotebookEditTool().run(
        notebook_path=str(nb),
        cell_number=1,
        new_source="## mid\n",
        cell_type="markdown",
        edit_mode="insert",
    )
    data = read_nb(nb)
    assert data["cells"][1]["cell_type"] == "markdown"
    assert data["cells"][1]["source"] == "## mid\n"
    assert len(data["cells"]) == 3


def test_delete(tmp_path: Path):
    clear_permissions()
    nb = setup_notebook(tmp_path)
    grant_write(tmp_path)

    NotebookEditTool().run(
        notebook_path=str(nb),
        cell_number=0,
        new_source="",  # unused
        edit_mode="delete",
    )
    data = read_nb(nb)
    assert len(data["cells"]) == 1
    assert data["cells"][0]["cell_type"] == "code"


def test_validation_errors(tmp_path: Path):
    nb = setup_notebook(tmp_path)
    # relative path
    with pytest.raises(ToolError):
        NotebookEditTool().run(
            notebook_path="demo.ipynb",
            cell_number=0,
            new_source="x",
        )
    # wrong extension
    txt = tmp_path / "foo.txt"
    txt.write_text("x")
    with pytest.raises(ToolError):
        NotebookEditTool().run(
            notebook_path=str(txt.resolve()),
            cell_number=0,
            new_source="x",
        )
