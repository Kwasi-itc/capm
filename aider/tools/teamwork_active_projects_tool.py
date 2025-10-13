"""
Tool: TeamworkActiveProjectsTool
--------------------------------

Fetches the *active projects metrics* from Teamwork.com by calling
``GET /projects/metrics/active.json`` via
:pyfunc:`aider.api.teamwork_projects.active_projects_metrics`.

It returns the JSON payload as a **string** so the token-counter never
receives a raw dict.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkActiveProjectsTool(BaseTool):
    """
    Tool that exposes Teamwork's *Active Projects Metrics* endpoint.
    """

    name = "teamwork_active_projects"
    description = (
        "Return the *active-projects* metrics from Teamwork by calling "
        "GET /projects/metrics/active.json.  The endpoint presently responds with "
        "a single counter (``{\"count\": <int>}``) but may expand over time.  The raw JSON "
        "payload is returned as a string so the token counter stays happy.  No positional "
        "arguments are required; extra kwargs become query parameters."
    )

    def run(self, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.active_projects_metrics(**kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
