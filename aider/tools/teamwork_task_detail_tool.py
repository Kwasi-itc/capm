"""
Tool: TeamworkTaskDetailTool
----------------------------

Retrieve the JSON representation for a single Teamwork task by calling
GET /tasks/{taskId}.json via aider.api.teamwork_projects.get_task.

Keyword arguments are forwarded verbatim as query-string parameters,
allowing advanced filters such as custom field constraints
(`customField[10][eq]=Option1`).

The JSON body is returned as a UTF-8 string.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkTaskDetailTool(BaseTool):
    """Expose Teamwork’s *Get a Task* endpoint."""

    name = "teamwork_task_detail"
    description = (
        "Retrieve the full JSON representation of a single Teamwork task via "
        "GET /tasks/{taskId}.json. Provide the numeric `task_id` and optionally any "
        "query-string filters supported by the endpoint – including advanced custom-field "
        "constraints such as `customField[10][eq]=Option1`. The response body is returned, "
        "JSON-encoded, as a string."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer", "description": "Numeric Teamwork task ID"},
        },
        "required": ["task_id"],
        "additionalProperties": True,
    }

    def run(self, task_id: int, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.get_task(task_id, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
