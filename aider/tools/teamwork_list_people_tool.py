"""
Tool: TeamworkListPeopleTool
----------------------------

Fetch the list of **people** (users, collaborators, contacts) that the
authenticated account can access by calling
GET /projects/api/v3/people.json through
:pyfunc:`aider.api.teamwork_projects.list_people`.

All query-string parameters accepted by Teamwork’s *List people* endpoint may be
passed as keyword arguments.  Common filters include:

• userType="account|collaborator|contact"  
• updatedAfter="YYYY-MM-DDTHH:MM:SSZ"  
• searchTerm="text"  
• orderMode="asc|desc", orderBy="name|namecaseinsensitive|company"  
• lastLoginAfter="…"  
• pageSize=50, page=1, skipCounts=False, showDeleted=False, …  

The raw JSON response is returned **as a UTF-8 string**.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool, ToolError
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkListPeopleTool(BaseTool):
    """Tool that wraps Teamwork’s *List people* endpoint."""

    name = "teamwork_list_people"
    description = (
        "Retrieve people (users, collaborators, contacts) visible to the authenticated user "
        "by issuing GET /people.json. Any query parameters accepted by Teamwork’s endpoint can "
        "be supplied as keyword arguments such as userType, updatedAfter, searchTerm, orderBy, "
        "orderMode, pageSize, page, skipCounts, showDeleted, etc. The raw JSON response is "
        "returned as a UTF-8 string."
    )

    # Allow arbitrary query params; document a core subset for UI / function calling
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "userType": {
                "type": "string",
                "description": "Filter by user type: account | collaborator | contact",
            },
            "updatedAfter": {"type": "string", "description": "ISO datetime filter"},
            "searchTerm": {"type": "string", "description": "Free-text search"},
            "orderMode": {
                "type": "string",
                "enum": ["asc", "desc"],
                "description": "Sort order direction (default asc)",
            },
            "orderBy": {
                "type": "string",
                "enum": ["name", "namecaseinsensitive", "company"],
                "description": "Field to sort by (default name)",
            },
            "lastLoginAfter": {"type": "string", "description": "ISO datetime filter"},
            "pageSize": {
                "type": "integer",
                "minimum": 1,
                "maximum": 500,
                "description": "Items per page (default 50)",
            },
            "page": {"type": "integer", "description": "Page number (default 1)"},
            "skipCounts": {"type": "boolean"},
            "showDeleted": {"type": "boolean"},
            "orderPrioritiseCurrentUser": {"type": "boolean"},
            "onlySiteOwner": {"type": "boolean"},
        },
        "additionalProperties": True,
    }

    def run(self, **query_params: Dict[str, Any]):  # noqa: D401
        """GET the people list and return the raw JSON string."""
        try:
            resp = tw_projects.list_people(**query_params)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            raise ToolError(f"Unexpected error: {exc}") from exc
