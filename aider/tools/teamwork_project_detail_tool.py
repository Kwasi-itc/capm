"""
Tool: TeamworkProjectDetailTool
-------------------------------

Fetch a single project from Teamwork.com with **optional advanced query
filters** (custom fields, status filters, etc.).

Internally calls :pyfunc:`aider.api.teamwork_projects.get_project_details`
and returns its JSON payload as a string.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkProjectDetailTool(BaseTool):
    """Expose Teamwork’s *Get Project* endpoint with filter support."""

    name = "teamwork_project_detail"
    description = (
        "Retrieve a single project by ID with optional query filters.  "
        "Positional argument ``project_id`` (int) is required.  Any additional "
        "keyword arguments are forwarded as query-string parameters, e.g. "
        "`projectCustomField[10][eq]='Option1'`, `includeCustomFields=True`, "
        "`orderMode='asc'`, etc."
    )

    def run(self, project_id: int, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.get_project_details(project_id, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
