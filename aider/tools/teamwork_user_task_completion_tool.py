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
        "Return task-completion metrics for one Teamwork *person* via "
        "GET /reporting/precanned/usertaskcompletion/{userId}.json.  "
        "Required parameter: `user_id` (integer).\n\n"
        "Optional query-string parameters you can pass (all are forwarded verbatim):\n"
        "  • userType              – account | collaborator | contact\n"
        "  • startDate / endDate   – date range window for the report (YYYY-MM-DD)\n"
        "  • updatedAfter          – ISO date-time, include records updated since\n"
        "  • searchTerm            – free-text search within comment content\n"
        "  • orderBy               – id | name | overduetasks | completedtasks | projects | …\n"
        "  • orderMode             – asc | desc  (default asc)\n"
        "  • pageSize / page       – pagination controls (defaults 50 / 1)\n"
        "  • teamIds, projectIds, jobRoleIds, ids – comma-separated ID filters\n"
        "  • selectedColumns       – comma-separated column list for custom report\n"
        "  • includeArchivedProjects, showDeleted, adminsOnly, skipCounts, onlySiteOwner …\n"
        "  • fields[...] selectors – eg fields[person]=id,firstName,lastName\n\n"
        "Any other parameter documented by Teamwork’s API is also accepted.  "
        "The endpoint’s JSON payload is returned unchanged – but JSON-encoded – "
        "so the token counter never sees a raw dictionary."
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
