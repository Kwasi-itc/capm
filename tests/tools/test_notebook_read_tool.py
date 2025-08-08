import json
from pathlib import Path

import pytest

from aider.permissions import clear_permissions, grant_read
from aider.tools.notebook_read_tool import NotebookReadTool, MAX_CELLS
from aider.tools.base_tool import ToolError


def make_nb(tmp: Path, name: str, cells) -> Path:
    nb = {
        "cells": cells,
        "metadata": {"language_info": {"name": "python"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    p = tmp / name
    p.write_text(json.dumps(nb), encoding="utf-8")
    return p


def demo_notebook(tmp: Path) -> Path:
    cells = [
        {"cell_type": "markdown", "source": ["# Title\n"]},
        {
            "cell_type": "code",
            "source": ["print('hi')\n"],
            "outputs": [{"output_type": "stream", "text": "hi\n"}],
        },
    ]
    return make_nb(tmp, "demo.ipynb", cells)


def test_read_notebook_basic(tmp_path: Path):
    clear_permissions()
    nb_path = demo_notebook(tmp_path)
    grant_read(tmp_path)

    out = NotebookReadTool().run(notebook_path=str(nb_path))
    assert "<cell 0>" in out and "<cell 1>" in out
    assert "print('hi')" in out and "hi" in out


def test_requires_absolute(tmp_path: Path):
    nb_path = demo_notebook(tmp_path)
    with pytest.raises(ToolError):
        NotebookReadTool().run(notebook_path="relative/path.ipynb")


def test_wrong_extension(tmp_path: Path):
    txt = tmp_path / "foo.txt"
    txt.write_text("x")
    with pytest.raises(ToolError):
        NotebookReadTool().run(notebook_path=str(txt.resolve()))


def test_permission_denied(tmp_path: Path):
    clear_permissions()
    nb_path = demo_notebook(tmp_path)
    with pytest.raises(ToolError):
        NotebookReadTool().run(notebook_path=str(nb_path))


def test_truncation(tmp_path: Path):
    clear_permissions()
    many_cells = [{"cell_type": "code", "source": [f"# {i}\n"]} for i in range(MAX_CELLS + 5)]
    nb_path = make_nb(tmp_path, "big.ipynb", many_cells)
    grant_read(tmp_path)

    out = NotebookReadTool().run(notebook_path=str(nb_path))
    assert "[[truncated" in out
