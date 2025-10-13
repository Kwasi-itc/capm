"""
Tool: TeamworkTaskSubtasksTool
------------------------------

Return the list of *sub-tasks* for a given Teamwork task by calling
GET /tasks/{taskId}/subtasks.json via
:pyfunc:`aider.api.teamwork_projects.task_subtasks`.

All keyword arguments are forwarded verbatim as query-string parameters,
enabling the full filter set supported by the endpoint (date ranges,
taskFilter presets, advanced custom-field filters, pagination, etc.).
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkTaskSubtasksTool(BaseTool):
    """Expose Teamwork’s *Get sub-tasks of a task* endpoint."""

    name = "teamwork_task_subtasks"
    description = (
        "List sub-tasks that belong to a parent task on Teamwork by calling "
        "GET /tasks/{taskId}/subtasks.json.  Provide the numeric `task_id`; any extra "
        "keyword arguments are forwarded as query-string parameters so you can use the full "
        "filter syntax supported by Teamwork (updatedAfter, taskFilter, customField[…], "
        "pagination, etc.). The endpoint’s JSON response is returned as a UTF-8 string."
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
            resp = tw_projects.task_subtasks(task_id, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
