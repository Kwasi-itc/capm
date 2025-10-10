"""Tool that exposes the Teamwork *Get all tasklists* endpoint.

It forwards any keyword arguments as query-string filters to
``aider.api.teamwork_projects.list_tasklists`` and returns the raw JSON
response body.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from aider.api.teamwork_projects import list_tasklists
from .base_tool import BaseTool, ToolError

logger = logging.getLogger(__name__)


class ListTasklistsTool(BaseTool):
    # ------------------------------------------------------------------ #
    # metadata for the LLM
    # ------------------------------------------------------------------ #
    name = "list_tasklists"
    description = (
        "Return all *task-lists* visible to the current user across every project.\n\n"
        "Common optional query parameters include (non-exhaustive):\n"
        "• updatedAfter (str ISO8601)\n"
        "• searchTerm (str) / projectType (str)\n"
        "• orderMode ('asc' | 'desc') & orderBy ('displayorder', 'name', …)\n"
        "• projectBudgetId (int)\n"
        "• pageSize (int, default 50) / page (int, default 1)\n"
        "• useFormulaFields (bool)\n"
        "• sortDefaultListFirst / sortActiveListsFirst (bool)\n"
        "• skipCounts (bool)\n"
        "• showPrivate / showDeleted / showCompleted (bool)\n"
        "• completedOnly (bool)\n"
        "• isReportDownload (bool)\n"
        "• includeArchivedProjects (bool) / getEmptyLists (bool)\n"
        "• projectIds / projectCompanyIds / ids (list[int])\n"
        "• include (list[str]) – nested resources to embed\n"
        "• fields[users|teams|tasks|tasklists|tags|projects|projectIntegrations|"
        "milestones|lockdowns|companies|ProjectPermissions] (list[str])"
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "updatedAfter": {"type": "string"},
            "searchTerm": {"type": "string"},
            "projectType": {"type": "string"},
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
                "description": "Nested objects to embed in the response.",
            },
            "ids": {"type": "array", "items": {"type": "integer"}},
            "projectIds": {"type": "array", "items": {"type": "integer"}},
            "projectCompanyIds": {"type": "array", "items": {"type": "integer"}},
        },
        "additionalProperties": True,
    }

    # ------------------------------------------------------------------ #
    # execution
    # ------------------------------------------------------------------ #
    def run(self, **query_params) -> str:  # noqa: D401
        """Execute the API request and return the JSON payload as a string."""
        logger.debug("Fetching global task-lists with %s", query_params)
        try:
            resp = list_tasklists(query=query_params)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"Teamwork API error: {exc}") from exc

        return resp.text
