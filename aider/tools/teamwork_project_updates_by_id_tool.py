"""
Tool: TeamworkProjectUpdatesByIdTool
------------------------------------

Fetches update posts for a *single* Teamwork project via
``GET /projects/{projectId}/updates.json`` by calling
:pyfunc:`aider.api.teamwork_projects.project_updates`.

All keyword arguments are forwarded as query parameters – for example
``updatedAfter="2024-01-01"``, ``orderBy="date" orderMode="desc"``,
``pageSize=100``, etc.

The JSON response is returned as a *string* to keep the upstream token
counter happy.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkProjectUpdatesByIdTool(BaseTool):
    """Expose Teamwork’s *projects/{id}/updates* endpoint."""

    name = "teamwork_project_updates_by_id"
    description = (
        "Return status-update messages for a *single* Teamwork project identified by the required "
        "positional argument ``project_id`` (int).  Additional keyword arguments are forwarded as "
        "query parameters, supporting the same filters as the global updates endpoint: "
        "`updatedAfter`, `createdAfter`, `orderBy`/`orderMode`, pagination (`pageSize`, `page`), "
        "boolean flags (`showDeleted`, `reactions`, `onlyStarredProjects`, …) and list filters "
        "such as `projectTagIds`, `projectOwnerIds`, etc."
    )

    def run(self, project_id: int, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.project_updates(project_id, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
