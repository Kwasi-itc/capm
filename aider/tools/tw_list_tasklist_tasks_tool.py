"""Tool that exposes the Teamwork *Get a task-list's tasks* endpoint.

Requires ``tasklistId`` and forwards any additional keyword arguments as
query-string parameters to ``aider.api.teamwork_projects.tasklist_tasks``.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from aider.api.teamwork_projects import tasklist_tasks
from .base_tool import BaseTool, ToolError

logger = logging.getLogger(__name__)


class ListTasklistTasksTool(BaseTool):
    # ------------------------------------------------------------------ #
    # metadata for the LLM
    # ------------------------------------------------------------------ #
    name = "list_tasklist_tasks"
    description = (
        "Return tasks that belong to a specific Teamwork *task-list*.\n\n"
        "Required parameter:\n"
        "• tasklistId (int) – Teamwork task-list ID\n\n"
        "Supports the extensive set of optional query parameters accepted by the "
        "API, such as updatedAfter/Before, taskFilter presets, priority, ordering, "
        "pagination, boolean flags (showDeleted, onlyUnplanned, matchAllTags, …) "
        "and advanced custom-field filtering using the syntax "
        "``customField[<id>][<op>]=value``."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "tasklistId": {
                "type": "integer",
                "description": "Numeric Teamwork task-list ID.",
            },
        },
        "required": ["tasklistId"],
        "additionalProperties": True,  # allow any extra query filters
    }

    # ------------------------------------------------------------------ #
    # execution
    # ------------------------------------------------------------------ #
    def run(self, tasklistId: int, **query_params) -> str:  # noqa: D401,N803
        """Execute the API request and return the JSON payload as a string."""
        logger.debug("Fetching tasks for task-list %s with %s", tasklistId, query_params)
        try:
            resp = tasklist_tasks(tasklistId, query=query_params)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"Teamwork API error: {exc}") from exc

        return resp.text
