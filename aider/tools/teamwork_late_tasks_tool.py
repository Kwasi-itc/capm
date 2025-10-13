"""
Tool: TeamworkLateTasksTool
---------------------------

Return the total number of *late* tasks from Teamwork.com by calling
GET /tasks/metrics/late.json via
:pyfunc:`aider.api.teamwork_projects.late_tasks_metrics`.

The JSON payload is returned **as a string** so the token-counter never
receives a raw dict.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkLateTasksTool(BaseTool):
    """Tool that exposes Teamwork's *Late Tasks Metrics* endpoint."""

    name = "teamwork_late_tasks"
    description = (
        "Return the total count of late tasks visible to the authenticated "
        "user by calling GET /tasks/metrics/late.json on Teamwork. "
        "No arguments are required. Any keyword arguments supplied are forwarded "
        "as query-string parameters."
    )

    def run(self, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.late_tasks_metrics(**kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
