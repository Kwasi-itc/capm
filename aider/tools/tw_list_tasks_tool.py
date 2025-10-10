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
        "Return all tasks the current user can access across every project and "
        "task-list.\n\n"
        "Supports the full suite of query parameters accepted by the Teamwork "
        "API, such as updatedAfter/Before, taskFilter presets, priority, "
        "ordering, pagination, boolean flags (showDeleted, onlyUnplanned, "
        "completedOnly, skipCounts, …), list filters (tags, tasklistIds, "
        "projectIds, projectStatuses, …) and advanced custom-field filtering "
        "using the syntax ``customField[<id>][<op>]=value``."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
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
