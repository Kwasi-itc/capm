"""Tool that exposes the Teamwork *List project categories* endpoint.

This tool is intended for LLM function-calling.  It forwards the user-supplied
arguments to ``aider.api.teamwork_projects.list_project_categories`` and
returns the raw JSON payload.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from aider.api.teamwork_projects import list_project_categories
from .base_tool import BaseTool, ToolError

logger = logging.getLogger(__name__)


class ListProjectCategoriesTool(BaseTool):
    # ------------------------------------------------------------------ #
    # metadata exposed to the LLM
    # ------------------------------------------------------------------ #
    name = "list_project_categories"
    description = (
        "Retrieve the catalogue of *project categories* visible to the current "
        "user, including colour, parent-child hierarchy and project counts. "
        "Allows filtering by name, starred-project flag, project status, specific "
        "IDs and selective field projection."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "searchTerm": {
                "type": "string",
                "description": "Filter categories by name (case-insensitive substring).",
            },
            "onlyStarredProjects": {
                "type": "boolean",
                "description": "Restrict task counts to *starred* projects.",
            },
            "projectStatuses": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Only include task counts from projects whose status matches one "
                    "of the provided values (active, late, upcoming, …)."
                ),
            },
            "ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Restrict the list to specific category IDs.",
            },
            "fields": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["id", "name", "color", "count", "parent", "parentId"],
                },
                "description": (
                    "Limit the returned object keys.  Maps to Teamwork’s "
                    "``fields[projectcategories]`` query parameter."
                ),
            },
        },
        "additionalProperties": False,
    }

    # ------------------------------------------------------------------ #
    # main execution
    # ------------------------------------------------------------------ #
    def run(
        self,
        searchTerm: Optional[str] = None,
        onlyStarredProjects: Optional[bool] = None,
        projectStatuses: Optional[List[str]] = None,
        ids: Optional[List[int]] = None,
        fields: Optional[List[str]] = None,
    ) -> str:  # noqa: D401
        """Execute the API request and return the raw JSON response body."""
        # Build query dict, mapping *fields* to Teamwork’s bracket notation
        params: Dict[str, Any] = {}

        if searchTerm is not None:
            params["searchTerm"] = searchTerm

        if onlyStarredProjects is not None:
            params["onlyStarredProjects"] = onlyStarredProjects

        if projectStatuses:
            params["projectStatuses"] = projectStatuses

        if ids:
            params["ids"] = ids

        if fields:
            params["fields[projectcategories]"] = fields

        logger.debug("Calling Teamwork list_project_categories with %s", params)
        try:
            resp = list_project_categories(query=params)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"Teamwork API error: {exc}") from exc

        return resp.text
