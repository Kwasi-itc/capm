"""
Tool package entry-point.

`discover_tools()` dynamically imports all modules in this package
(except base_tool) and returns every concrete subclass of BaseTool.
"""
from importlib import import_module
from pathlib import Path
from typing import List, Type

from .base_tool import BaseTool


def discover_tools() -> List[Type[BaseTool]]:
    pkg_dir = Path(__file__).parent

    # Import every *.py file (except specials and base_tool)
    for py in pkg_dir.glob("*.py"):
        if py.name in {"__init__.py", "base_tool.py"}:
            continue
        import_module(f"{__name__}.{py.stem}")

    # Return all concrete subclasses discovered so far
    return [
        cls
        for cls in BaseTool.__subclasses__()
        if cls is not BaseTool and cls.name  # skip abstract / unnamed
    ]


__all__ = ["BaseTool", "discover_tools", "RepoMapTool"]
