"""
Tool: TeamworkNotebooksTool
---------------------------

List notebooks visible to the authenticated Teamwork user by calling
GET /notebooks.json via :pyfunc:`aider.api.teamwork_projects.list_notebooks`.

All keyword arguments are forwarded verbatim as query-string parameters
so callers can leverage the endpoint’s extensive filter set.

The JSON response is returned **as a string** (UTF-8 encoded).
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkNotebooksTool(BaseTool):
    """Expose Teamwork’s *List notebooks* endpoint."""

    name = "teamwork_notebooks"
    description = (
        "Return notebooks visible to the authenticated Teamwork account by issuing "
        "GET /notebooks.json. Accepts all filters supported by the endpoint – date ranges "
        "(updatedAfter, createdAfter), searchTerm, project filters, orderBy/orderMode, "
        "pagination (pageSize/page), Boolean flags (secureOnly, lockedOnly, showDeleted, …), "
        "list filters (tagIds, projectTagIds, projectIds, projectOwnerIds, …), include and "
        "fields[...] selectors. The raw JSON payload is returned as a UTF-8 string."
    )
    # No required properties – every parameter is optional and forwarded
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "updatedAfter": {"type": "string"},
            "createdAfter": {"type": "string"},
            "searchTerm": {"type": "string"},
            "projectType": {
                "type": "string",
                "enum": ["normal", "tasklists-template", "projects-template"],
            },
            "projectStatuses": {"type": "string"},
            "orderBy": {
                "type": "string",
                "enum": ["name", "project", "dateCreated", "dateUpdated", "category"],
            },
            "orderMode": {"type": "string", "enum": ["asc", "desc"]},
            "pageSize": {"type": "integer", "minimum": 1},
            "page": {"type": "integer", "minimum": 1},
            "secureOnly": {"type": "boolean"},
            "lockedOnly": {"type": "boolean"},
            "showDeleted": {"type": "boolean"},
            "skipCounts": {"type": "boolean"},
        },
        "required": [],
        "additionalProperties": True,
    }

    def run(self, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.list_notebooks(**kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
