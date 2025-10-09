"""
Tool: TeamworkProjectsOwnersTool
--------------------------------

Fetches *owner metrics* from Teamwork.com by calling
``GET /projects/metrics/owners.json`` via
:pyfunc:`aider.api.teamwork_projects.owners_projects_metrics`.

It returns the JSON payload as a **string** so token counting is safe.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkProjectsOwnersTool(BaseTool):
    """Expose Teamwork’s *projects/metrics/owners* endpoint."""

    name = "teamwork_projects_owners"
    description = (
        "Return the number of projects per project owner (plus unassigned).  "
        "Supports the same filters as the Teamwork owners-metrics endpoint, e.g.\n"
        "  • orderMode='asc' | 'desc' (default desc)\n"
        "  • pageSize=50, page=1, skipCounts=True/False\n"
        "  • onlyStarredProjects=True, matchAllProjectTags=True\n"
        "  • projectTagIds=[1,2], projectStatuses=['active','late'], projectOwnerIds=[99], …"
    )

    def run(self, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.owners_projects_metrics(**kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
