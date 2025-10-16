"""
Tool: TeamworkProjectPeopleTool
-------------------------------

Fetch the list of **people on a specific project** by calling
GET /projects/{projectId}/people.json through
:pyfunc:`aider.api.teamwork_projects.project_people`.

Required parameter
------------------
• project_id (int) – Teamwork project ID

Optional keyword arguments correspond to the query-string filters accepted by
the endpoint (userType, updatedAfter, searchTerm, orderBy, orderMode, pageSize,
page, skipCounts, showDeleted, orderPrioritiseCurrentUser, onlySiteOwner,
onlyOwnerCompany, includeServiceAccounts, includeObservers, includeCollaborators,
includeClients, …).

The raw JSON response is returned **as a UTF-8 string**.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool, ToolError
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkProjectPeopleTool(BaseTool):
    """Tool that wraps Teamwork’s *Project People* endpoint."""

    name = "teamwork_project_people"
    description = (
        "List people (users, collaborators, contacts) assigned to a single project by issuing "
        "GET /projects/{projectId}/people.json. Provide the numeric `project_id` and any optional "
        "query parameters accepted by Teamwork such as userType, updatedAfter, searchTerm, orderBy, "
        "orderMode, pageSize, page, skipCounts, showDeleted, onlyOwnerCompany, etc. "
        "The raw JSON response is returned as a UTF-8 string."
    )

    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "Numeric Teamwork project ID.",
            },
            # expose the most common filters; allow additional params freely
            "userType": {
                "type": "string",
                "description": "User type: account | collaborator | contact",
            },
            "updatedAfter": {"type": "string", "description": "ISO datetime filter"},
            "searchTerm": {"type": "string", "description": "Free-text search"},
            "orderMode": {"type": "string", "enum": ["asc", "desc"]},
            "orderBy": {
                "type": "string",
                "enum": ["name", "namecaseinsensitive", "company"],
            },
            "lastLoginAfter": {"type": "string"},
            "pageSize": {"type": "integer", "minimum": 1, "maximum": 500},
            "page": {"type": "integer"},
            "skipCounts": {"type": "boolean"},
            "showDeleted": {"type": "boolean"},
            "orderPrioritiseCurrentUser": {"type": "boolean"},
            "onlySiteOwner": {"type": "boolean"},
            "onlyOwnerCompany": {"type": "boolean"},
            "includeServiceAccounts": {"type": "boolean"},
            "includeObservers": {"type": "boolean"},
            "includeCollaborators": {"type": "boolean"},
            "includeClients": {"type": "boolean"},
        },
        "required": ["project_id"],
        "additionalProperties": True,
    }

    def run(self, project_id: int, **query_params: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.project_people(project_id, **query_params)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            raise ToolError(f"Unexpected error: {exc}") from exc
