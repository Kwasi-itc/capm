"""Tool that exposes the Teamwork *Get all tasks* endpoint.

It forwards any keyword arguments as query-string filters to
``aider.api.teamwork_projects.list_tasks`` and returns the raw JSON payload.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from aider.api.teamwork_projects import list_tasks
from .base_tool import BaseTool, ToolError

logger = logging.getLogger(__name__)


class ListTasksTool(BaseTool):
    # ------------------------------------------------------------------ #
    # metadata for LLM
    # ------------------------------------------------------------------ #
    name = "list_tasks"
    description = (
        "List *tasks* across all projects and task-lists visible to the current "
        "user.\n\n"
        "Common query parameters (non-exhaustive):\n"
        "• updatedAfter / updatedBefore (str ISO8601)\n"
        "• dueAfter / dueBefore (str ISO8601)\n"
        "• createdAfter / createdBefore (str ISO8601)\n"
        "• completedAfter / completedBefore (str ISO8601)\n"
        "• taskFilter (str) – all, overdue, completed, today, …\n"
        "• searchTerm (str)\n"
        "• priority (str)\n"
        "• orderMode ('asc'|'desc') & orderBy (duedate, priority, createdat, …)\n"
        "• pageSize (int, default 50) & page (int)\n"
        "• Boolean flags – showDeleted, showCompleted, completedOnly, skipCounts, "
        "onlyUnplanned, sortActiveFirst, nestSubTasks, matchAllTags, …\n"
        "• List filters – tags (list[str]), tagIds (list[int]), tasklistIds, "
        "projectIds, projectCompanyIds, projectStatuses, status (upcoming|late|all), …\n"
        "• Advanced custom-field filtering – ``customField[<id>][op]=value`` "
        "(op = like, not-like, eq, not, lt, gt, any)\n\n"
        "Any other parameter documented by Teamwork’s *Get all tasks* endpoint "
        "may also be supplied."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {},  # empty schema – rely on additionalProperties for flexibility
        "additionalProperties": True,  # schema left open due to huge parameter set
    }

    # ------------------------------------------------------------------ #
    # execution
    # ------------------------------------------------------------------ #
    def run(self, **query_params) -> str:  # noqa: D401
        """Execute the API request and return the JSON payload as a string."""
        logger.debug("Fetching global tasks with %s", query_params)
        try:
            resp = list_tasks(query=query_params)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"Teamwork API error: {exc}") from exc

        return resp.text
