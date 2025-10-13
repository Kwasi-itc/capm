"""
Tool: TeamworkCompletedTasksTool
--------------------------------

Return the total number of completed tasks from Teamwork.com by calling
GET /tasks/metrics/complete.json via
:pyfunc:`aider.api.teamwork_projects.completed_tasks_metrics`.

The JSON payload is returned **as a string** so the token-counter never
receives a raw dict.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkCompletedTasksTool(BaseTool):
    """Tool that exposes Teamwork's *Completed Tasks Metrics* endpoint."""

    name = "teamwork_completed_tasks"
    description = (
        "Fetch the total number of *completed* tasks the authenticated Teamwork user can access "
        "by calling GET /tasks/metrics/complete.json. The endpoint replies with a minimal JSON "
        "object such as {\"count\": 42}; this payload is forwarded unchanged – but JSON-encoded – "
        "back to the LLM.  No positional arguments are required; any additional keyword arguments "
        "are appended to the request as query-string parameters."
    )

    def run(self, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.completed_tasks_metrics(**kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
