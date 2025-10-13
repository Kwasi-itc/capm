"""
Tool: TeamworkDeleteTaskTool
----------------------------

Delete an existing Teamwork task (**and its subtasks**) by calling
DELETE /tasks/{taskId}.json through
:pyfunc:`aider.api.teamwork_projects.delete_task`.

Safety-first: the tool requires an explicit ``confirm=true`` argument
before it will execute the destructive call.  If the confirmation flag
is omitted or ``false`` the tool responds with an explanatory message
and **does not** perform the deletion.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool, ToolError
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkDeleteTaskTool(BaseTool):
    """Tool that deletes a Teamwork task after explicit confirmation."""

    name = "teamwork_delete_task"
    description = (
        "Permanently delete a task – and all of its subtasks – in Teamwork by issuing "
        "DELETE /tasks/{taskId}.json. Supply the numeric `task_id`.  Safety guard: pass "
        "confirm=true to skip the interactive yes/no prompt; otherwise the tool asks for "
        "confirmation in the console before proceeding. On success it returns "
        "{\"status\": \"deleted\", \"task_id\": <id>} or relays the API’s JSON error body."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer", "description": "Numeric Teamwork task ID"},
            "confirm": {
                "type": "boolean",
                "description": "Must be true to actually delete the task",
                "default": False,
            },
        },
        "required": ["task_id"],
    }

    def run(self, task_id: int, confirm: bool = False, **kwargs: Dict[str, Any]):  # noqa: D401
        # ------------------------------------------------------------------
        # Interactive safeguard
        # ------------------------------------------------------------------
        if not confirm:
            answer = input(
                f"Are you sure you want to DELETE task {task_id}? [y/N]: "
            ).strip().lower()
            if answer not in ("y", "yes"):
                return "Deletion cancelled."

        try:
            resp = tw_projects.delete_task(task_id, **kwargs)
            # Teamwork returns 204 No Content → fabricate a tiny JSON payload
            if resp.status_code == 204 or not resp.content:
                return json.dumps({"status": "deleted", "task_id": task_id}, ensure_ascii=False)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            raise ToolError(f"Unexpected error during deletion: {exc}") from exc
