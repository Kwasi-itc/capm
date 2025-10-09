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
        "Fetch the **project-updates feed** (status posts) across *all* projects the authenticated "
        "user can see.  Every keyword argument you supply is forwarded as a query-string parameter "
        "to Teamwork’s “updates” endpoint, so you can leverage its full filtering power:\n\n"
        "  • Date filters  updatedAfter / createdAfter (ISO 8601)\n"
        "  • Project filters projectId (int) projectStatus or projectStatuses "
        "(active|current|late|upcoming|completed|deleted)\n"
        "                     projectTagIds, projectOwnerIds, projectIds, "
        "projectHealths, projectCompanyIds, projectCategoryIds (each list[int])\n"
        "  • Ordering    orderBy=date|color|health|project|user  +  orderMode=asc|desc (def asc)\n"
        "  • Pagination   pageSize (def 50) page (def 1)\n"
        "  • Flags     skipCounts, showDeleted, reactions, onlyStarredProjects, "
        "includeArchivedProjects, emoji, activeOnly, matchAllProjectTags …\n\n"
        "The tool returns the endpoint’s JSON response **as a string** so it can be passed back to "
        "the LLM without triggering token-counting errors."
    )

    def run(self, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.list_project_updates(**kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
