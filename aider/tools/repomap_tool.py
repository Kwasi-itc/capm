"""
RepoMapTool – expose a condensed repository map to the LLM.

This tool leverages aider.repomap.RepoMap to generate a concise view of files
that are *not* already in the chat, helping the model reference wider context.
"""
from __future__ import annotations

from typing import List, Optional

from aider.repomap import RepoMap, find_src_files
from .base_tool import BaseTool, ToolError


class RepoMapTool(BaseTool):
    # ---------------- metadata visible to the LLM -----------------
    name = "repo_map"
    description = "Return a concise repository map of files not yet shared in chat."
    parameters = {
        "type": "object",
        "properties": {
            "chat_files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Paths of files already present in the chat context (optional).",
            },
            "other_files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Additional repo files to consider (optional).",
            },
            "max_tokens": {
                "type": "integer",
                "description": "Token budget for the generated map (optional).",
            },
        },
        "required": [],
    }

    # -------------------------- runtime ---------------------------
    def run(  # noqa: D401
        self,
        *,
        chat_files: Optional[List[str]] = None,
        other_files: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate and return a repo-map string.

        Raises
        ------
        ToolError
            If repo-map generation fails.
        """
        chat_files = chat_files or []
        if other_files is None:
            # Default to every file in the repo minus the ones already in chat
            other_files = [f for f in find_src_files(".") if f not in chat_files]
        else:
            other_files = other_files or []
        try:
            rm = RepoMap(root=".", io=self.io)
            if max_tokens is not None:
                rm.max_map_tokens = max_tokens
            return rm.get_repo_map(chat_files, other_files, force_refresh=True) or ""
        except Exception as exc:  # pragma: no cover
            raise ToolError(str(exc)) from exc


__all__ = ["RepoMapTool"]
