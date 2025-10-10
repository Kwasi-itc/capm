"""Tool that exposes the Teamwork *Create task* endpoint.

It creates a new task in the given task-list.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from aider.api.teamwork_projects import create_task
from .base_tool import BaseTool, ToolError

logger = logging.getLogger(__name__)


class CreateTaskTool(BaseTool):
    # ------------------------------------------------------------------ #
    # metadata for the LLM
    # ------------------------------------------------------------------ #
    name = "create_task"
    description = (
        "Create a new task inside a specific Teamwork *task-list*.\n\n"
        "Required parameters:\n"
        "• tasklistId (int) – the task-list to create the task in\n"
        "• task (object) – Task details (name, description, dates, assignees …)\n\n"
        "Optional parameters mirror the Teamwork API body structure and may "
        "include attachments, tags, taskOptions, card, workflows, predecessors, "
        "attachmentOptions, etc."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "tasklistId": {
                "type": "integer",
                "description": "Numeric Teamwork task-list ID that will receive the task.",
            },
            # We keep the schema flexible: allow arbitrary keys except tasklistId
        },
        "required": ["tasklistId", "task"],
        "additionalProperties": True,
    }

    # ------------------------------------------------------------------ #
    # execution
    # ------------------------------------------------------------------ #
    def run(self, tasklistId: int, **body_params) -> str:  # noqa: D401,N803
        """POST the task creation payload and return the response body."""
        logger.debug("Creating task in task-list %s with %s", tasklistId, body_params)

        # Build JSON body excluding tasklistId
        json_body = {k: v for k, v in body_params.items() if k != "tasklistId"}

        try:
            resp = create_task(tasklistId, data=json_body)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"Teamwork API error: {exc}") from exc

        return resp.text
