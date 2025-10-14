"""
Tool: TeamworkSearchTool
------------------------

Run a cross-resource search against the Teamwork API by calling
GET /search.json via :pyfunc:`aider.api.teamwork_projects.search`.

Required parameters
-------------------
• search_for  (string) – resource name (projects, tasks, messages, …)  
• search_term (string) – query string, already URL-encoded if necessary

Optional keyword arguments become query parameters (projectId, sortOrder,
includeArchivedProjects, includeCompletedItems, pageSize).

The JSON response is returned **as a UTF-8 string**.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkSearchTool(BaseTool):
    """Expose Teamwork’s global *Search* endpoint."""

    name = "teamwork_search"
    description = (
        "Perform a full-text search across Teamwork resources by issuing "
        "GET /search.json. Two parameters are required: `search_for` (resource name such as "
        "`projects`, `tasks`, `messages`, etc.) and `search_term` (the query string). "
        "Optional keyword arguments – `projectId`, `sortOrder=asc|desc`, "
        "`includeArchivedProjects`, `includeCompletedItems`, `pageSize` – are appended "
        "to the query string. The raw JSON payload is returned as a UTF-8 string."
    )

    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "search_for": {
                "type": "string",
                "description": "Resource to search in (projects, notebooks, files, tasks, …)",
            },
            "search_term": {
                "type": "string",
                "description": "Search expression (URL-encoded if it contains special chars)",
            },
            "projectId": {"type": "integer"},
            "sortOrder": {"type": "string", "enum": ["asc", "desc"]},
            "includeArchivedProjects": {"type": "boolean"},
            "includeCompletedItems": {"type": "boolean"},
            "pageSize": {"type": "integer", "minimum": 1},
        },
        "required": ["search_for", "search_term"],
        "additionalProperties": True,
    }

    def run(
        self,
        search_for: str,
        search_term: str,
        **kwargs: Dict[str, Any],
    ):  # noqa: D401
        try:
            resp = tw_projects.search(search_for, search_term, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
