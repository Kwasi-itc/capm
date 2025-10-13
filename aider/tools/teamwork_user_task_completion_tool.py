"""
Tool: TeamworkUserTaskCompletionTool
------------------------------------

Return task-completion statistics for an individual Teamwork user by
calling GET
``/reporting/precanned/usertaskcompletion/{userId}.json`` through
:pyfunc:`aider.api.teamwork_projects.user_task_completion`.

Input
-----
• user_id (int, required) – Teamwork person ID  
• All additional keyword arguments are forwarded as query-string
  parameters so callers can take advantage of the endpoint’s extensive
  filter set (date ranges, orderBy, userType, pagination, list filters,
  fields[…], etc.).

The JSON response is returned **as a string** for token-counter safety.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkUserTaskCompletionTool(BaseTool):
    """Expose Teamwork's *User Task-Completion* precanned report."""

    name = "teamwork_user_task_completion"
    description = (
        "Retrieve task-completion statistics for a single Teamwork user by calling "
        "GET /reporting/precanned/usertaskcompletion/{userId}.json.  Supply `user_id` "
        "and optionally any query parameters supported by the endpoint (userType, "
        "startDate/endDate, orderBy/orderMode, teamIds, projectIds, fields[…], etc.). "
        "The JSON response is returned as a UTF-8 string."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "user_id": {"type": "integer", "description": "Numeric Teamwork person ID"},
        },
        "required": ["user_id"],
        "additionalProperties": True,
    }

    def run(self, user_id: int, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.user_task_completion(user_id, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
