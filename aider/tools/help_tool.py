"""
HelpTool – lists all available tools and their short descriptions.

This tool can be called from the LLM to discover what helpers are
available inside the `aider.tools` package.  It dynamically inspects the
loaded subclasses of `BaseTool`, so anything already imported and
registered will automatically be included in the output.

If new tools are added at runtime and imported before `HelpTool.run` is
invoked, they will show up in the listing without further modification.
"""
from __future__ import annotations

from .base_tool import BaseTool


class HelpTool(BaseTool):
    # ------------------- metadata shown to the LLM --------------------
    name = "help"
    description = "Return the names and human-oriented descriptions of all available tools."

    # ----------------- tool implementation details -------------------
    args_schema = None  # This tool takes no parameters.

    def run(self) -> str:  # noqa: D401
        """
        Produce a newline-separated list of tools in the form:

            <name> – <description>

        The list is sorted alphabetically by tool name, and the HelpTool
        itself is omitted from the results to avoid recursion.
        """
        lines: list[str] = []

        # Iterate over *currently imported* subclasses of BaseTool.
        for cls in BaseTool.__subclasses__():
            if cls is HelpTool:
                # Skip listing ourselves.
                continue

            tool_name = getattr(cls, "name", cls.__name__)
            tool_desc = getattr(cls, "description", "").strip() or "(no description)"
            lines.append(f"{tool_name} – {tool_desc}")

        # Sort for stable, predictable ordering.
        lines.sort(key=str.lower)
        return "\n".join(lines)
