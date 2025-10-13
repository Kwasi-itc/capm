"""
Tool: TeamworkCreateSubtaskTool
-------------------------------

Create a **new sub-task** under a parent task in Teamwork by calling
POST /tasks/{taskId}/subtasks.json via
:pyfunc:`aider.api.teamwork_projects.create_subtask`.

Input
-----
• task_id (int, required) – parent task ID  
• payload (object, required) – JSON body accepted by Teamwork’s endpoint
  (keys: task, tags, attachments, taskOptions, card, workflows, …).

Any additional keyword arguments are forwarded to ``requests.post`` so
callers can pass headers, timeouts, etc.

The endpoint returns the freshly created task object, which is relayed
back as a UTF-8 JSON string.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool, ToolError
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkCreateSubtaskTool(BaseTool):
    """Tool that wraps Teamwork’s *Create Sub-task* endpoint."""

    name = "teamwork_create_subtask"
    description = (
        "Create a new sub-task beneath an existing parent task by issuing "
        "POST /tasks/{taskId}/subtasks.json. Provide the numeric `task_id` and a `payload` "
        "object that matches Teamwork’s JSON schema (task, tags, attachments, …). "
        "The newly created task is returned as a JSON string."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer", "description": "Numeric parent task ID"},
            "payload": {
                "type": "object",
                "description": "JSON body to submit (task / tags / attachments / …)",
            },
        },
        "required": ["task_id", "payload"],
        "additionalProperties": False,
    }

    def run(self, task_id: int, payload: Dict[str, Any], **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.create_subtask(task_id, payload, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            raise ToolError(f"Unexpected error: {exc}") from exc
