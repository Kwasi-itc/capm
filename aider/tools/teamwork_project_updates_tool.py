"""
Tool: TeamworkProjectUpdatesTool
--------------------------------

Fetches project-update messages across all accessible projects via
``GET /projects/updates.json`` (wrapper:
:pyfunc:`aider.api.teamwork_projects.list_project_updates`).

All keyword arguments are forwarded as query parameters – for instance
``updatedAfter="2024-01-01"`, ``projectStatus="active"``,
``orderBy="date" orderMode="desc"``, ``projectTagIds=[4,7]``, etc.

The JSON response is returned as a *string* so token counting never sees
a raw dict.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkProjectUpdatesTool(BaseTool):
    """Expose Teamwork’s *projects/updates* endpoint."""

    name = "teamwork_project_updates"
    description = (
        "Return project-update messages for all projects the authenticated user can access.  "
        "Supports every filter documented by Teamwork’s updates endpoint, such as "
        "`updatedAfter`, `createdAfter`, `projectStatus`, `orderBy`/`orderMode`, "
        "`projectId`, pagination (`pageSize`, `page`), boolean toggles "
        "(`skipCounts`, `showDeleted`, `reactions`, `onlyStarredProjects`, …) and list-style "
        "filters like `projectTagIds`, `projectStatuses`, `projectOwnerIds`, etc."
    )

    def run(self, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.list_project_updates(**kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
