"""Tool that exposes the Teamwork *Get tasklists in a project* endpoint.

It requires a ``projectId`` and forwards any other keyword arguments as
query-string filters to ``aider.api.teamwork_projects.project_tasklists``.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from aider.api.teamwork_projects import project_tasklists
from .base_tool import BaseTool, ToolError

logger = logging.getLogger(__name__)


class ListProjectTasklistsTool(BaseTool):
    # ------------------------------------------------------------------ #
    # metadata for the LLM
    # ------------------------------------------------------------------ #
    name = "list_project_tasklists"
    description = (
        "Return all *task-lists* within a specified Teamwork project, with "
        "optional server-side filtering (updatedAfter, searchTerm, projectType…), "
        "rich sorting, pagination and the ability to embed related resources "
        "(defaultTasks, milestones, companies, workflow stages, …)."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "projectId": {
                "type": "integer",
                "description": "Numeric Teamwork project ID to retrieve task-lists from.",
            },
            "updatedAfter": {"type": "string"},
            "searchTerm": {"type": "string"},
            "orderMode": {"type": "string", "enum": ["asc", "desc"]},
            "orderBy": {
                "type": "string",
                "enum": ["displayorder", "name", "status", "createdat", "updatedat", "project"],
            },
            "pageSize": {"type": "integer"},
            "page": {"type": "integer"},
            "showPrivate": {"type": "boolean"},
            "showDeleted": {"type": "boolean"},
            "showCompleted": {"type": "boolean"},
            "completedOnly": {"type": "boolean"},
            "include": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Additional, nested objects to include in the response.",
            },
            "ids": {"type": "array", "items": {"type": "integer"}},
            "projectIds": {"type": "array", "items": {"type": "integer"}},
        },
        "required": ["projectId"],
        "additionalProperties": True,  # allow any other query parameters
    }

    # ------------------------------------------------------------------ #
    # execution
    # ------------------------------------------------------------------ #
    def run(self, projectId: int, **query_params) -> str:  # noqa: D401,N803
        """Execute the API request and return the raw JSON response body."""
        logger.debug("Fetching task-lists for project %s with %s", projectId, query_params)
        try:
            resp = project_tasklists(projectId, query=query_params)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"Teamwork API error: {exc}") from exc

        return resp.text
