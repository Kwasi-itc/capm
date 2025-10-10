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
        "Return all *task-lists* within a specified Teamwork project.\n\n"
        "Required parameter:\n"
        "• projectId (int) – Teamwork project ID\n\n"
        "Common optional query parameters include:\n"
        "• updatedAfter (str ISO8601)\n"
        "• searchTerm (str)\n"
        "• projectType (str)\n"
        "• orderMode ('asc' | 'desc')\n"
        "• orderBy ('displayorder', 'name', 'status', 'createdat', 'updatedat', 'project')\n"
        "• projectBudgetId (int)\n"
        "• pageSize (int, default 50) / page (int, default 1)\n"
        "• useFormulaFields (bool)\n"
        "• sortDefaultListFirst / sortActiveListsFirst (bool)\n"
        "• skipCounts (bool)\n"
        "• showPrivate / showDeleted / showCompleted (bool)\n"
        "• completedOnly (bool)\n"
        "• isReportDownload (bool)\n"
        "• includeArchivedProjects (bool)\n"
        "• getEmptyLists (bool)\n"
        "• projectIds / projectCompanyIds / ids (list[int])\n"
        "• include (list[str]) – nested resources to embed\n"
        "• fields[users|teams|tasks|tasklists|tags|projects|projectIntegrations|"
        "milestones|lockdowns|companies|ProjectPermissions] (list[str]) – "
        "limit returned fields"
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
