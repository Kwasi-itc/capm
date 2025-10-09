"""
Tool: TeamworkProjectsHealthTool
--------------------------------

Fetches project-health metrics from Teamwork.com by calling
``GET /projects/metrics/healths.json`` via
:pyfunc:`aider.api.teamwork_projects.health_projects_metrics`.

Any keyword arguments you pass are forwarded as query parameters
(``projectStatus="active"``, ``onlyStarredProjects=True``,
``projectTagIds=[1,2]`` …).  The result is returned as a JSON **string**
so the upstream token counter never sees a raw dict.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkProjectsHealthTool(BaseTool):
    """Expose Teamwork’s *projects/metrics/healths* endpoint."""

    name = "teamwork_projects_health"
    description = (
        "Return the number of projects in each health category (good/ok/bad/not_set) that the "
        "authenticated user can access.  Accepts the same filters as Teamwork’s endpoint, e.g. "
        "`projectStatus=\"active\"`, `onlyStarredProjects=True`, `projectTagIds=[1,2]`, etc."
    )

    def run(self, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.health_projects_metrics(**kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
