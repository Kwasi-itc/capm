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
        "Required path parameter:\n"
        "• tasklistId (int) – ID of the parent task-list\n\n"
        "JSON body parameters:\n"
        "• task (object, required) – core task details (name, description, dates, assignees …)\n"
        "• tags (array[object]) – tag objects to attach\n"
        "• attachmentOptions (object) – options for handling file attachments\n"
        "• attachments (object) – existing or uploaded attachments to link\n"
        "• taskOptions (object) – additional task flags/options\n"
        "• workflows (object) – workflow placement information\n"
        "• card (object) – Kanban card metadata\n"
        "• predecessors (array[object]) – predecessor task definitions"
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "tasklistId": {
                "type": "integer",
                "description": "Numeric Teamwork task-list ID that will receive the task.",
            },
            "task": {
                "type": "object",
                "description": "Core task information such as name, description, dates, assignees, etc.",
            },
            "tags": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Tag objects to assign to the task.",
            },
            "attachmentOptions": {
                "type": "object",
                "description": "Options controlling attachment handling.",
            },
            "attachments": {
                "type": "object",
                "description": "Attachment payload linking existing or uploaded files.",
            },
            "taskOptions": {
                "type": "object",
                "description": "Additional task options and flags.",
            },
            "workflows": {
                "type": "object",
                "description": "Information about workflow stage/column placement.",
            },
            "card": {
                "type": "object",
                "description": "Kanban card metadata associated with the task.",
            },
            "predecessors": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Predecessor relations for the new task.",
            },
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
