"""Tool that exposes the Teamwork *Get specific tasklist* endpoint.

Requires ``tasklistId`` and forwards any additional keyword arguments as
query-string parameters to ``aider.api.teamwork_projects.get_tasklist``.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from aider.api.teamwork_projects import get_tasklist
from .base_tool import BaseTool, ToolError

logger = logging.getLogger(__name__)


class GetTasklistTool(BaseTool):
    # ------------------------------------------------------------------ #
    # metadata for the LLM
    # ------------------------------------------------------------------ #
    name = "get_tasklist"
    description = (
        "Retrieve a single Teamwork *task-list* by ID.  Supports the same optional "
        "query parameters as the list endpoints, such as include, fields[…], "
        "showPrivate/deleted/completed flags, ordering and pagination."
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
        "additionalProperties": True,  # allow any extra query params
    }

    # ------------------------------------------------------------------ #
    # execution
    # ------------------------------------------------------------------ #
    def run(self, tasklistId: int, **query_params) -> str:  # noqa: D401,N803
        """Execute the API request and return the JSON response body."""
        logger.debug("Fetching task-list %s with %s", tasklistId, query_params)
        try:
            resp = get_tasklist(tasklistId, query=query_params)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"Teamwork API error: {exc}") from exc

        return resp.text
