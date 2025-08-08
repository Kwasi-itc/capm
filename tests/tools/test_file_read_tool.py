import base64
from pathlib import Path

import pytest
from PIL import Image

from aider.permissions import clear_permissions, grant_read
from aider.tools.file_read_tool import FileReadTool, MAX_OUTPUT_SIZE
from aider.tools.base_tool import ToolError


def make_text(tmp: Path, name: str, lines: int = 10) -> Path:
    p = tmp / name
    p.write_text("".join(f"{i}\n" for i in range(lines)))
    return p


def make_image(tmp: Path, name: str) -> Path:
    p = tmp / name
    Image.new("RGB", (8, 8), color="red").save(p)
    return p


def test_read_text_basic(tmp_path: Path):
    clear_permissions()
    grant_read(tmp_path)

    f = make_text(tmp_path, "a.txt", 5)
    out = FileReadTool().run(file_path=str(f))
    assert "showing 1-5 of 5" in out
    assert "0\n1\n2\n" in out


def test_offset_limit(tmp_path: Path):
    clear_permissions()
    grant_read(tmp_path)

    f = make_text(tmp_path, "b.txt", 50)
    out = FileReadTool().run(file_path=str(f), offset=11, limit=5)
    assert "showing 11-15" in out
    assert "10\n11\n12\n13\n14" in out


def test_large_file_requires_paging(tmp_path: Path):
    clear_permissions()
    grant_read(tmp_path)

    big = tmp_path / "big.txt"
    big.write_text("x" * (MAX_OUTPUT_SIZE + 100))
    with pytest.raises(ToolError):
        FileReadTool().run(file_path=str(big))


def test_read_image(tmp_path: Path):
    clear_permissions()
    grant_read(tmp_path)

    img = make_image(tmp_path, "pic.png")
    out = FileReadTool().run(file_path=str(img))
    header, payload = out.split(",", 1)
    assert header.startswith("data:image/png;base64")
    base64.b64decode(payload)


def test_ipynb_refusal(tmp_path: Path):
    clear_permissions()
    grant_read(tmp_path)

    nb = tmp_path / "demo.ipynb"
    nb.write_text("{}")
    with pytest.raises(ToolError):
        FileReadTool().run(file_path=str(nb))


def test_permission_denied(tmp_path: Path):
    clear_permissions()
    secret = make_text(tmp_path, "secret.txt")
    with pytest.raises(ToolError):
        FileReadTool().run(file_path=str(secret))
