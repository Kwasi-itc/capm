"""
Tool: TeamworkAddProjectPeopleTool
----------------------------------

Add **people** (users) to an existing Teamwork project by calling
PUT /projects/{projectId}/people.json through
:pyfunc:`aider.api.teamwork_projects.add_project_people`.

Required parameters
-------------------
• project_id (int) – Teamwork project ID  
• payload    (object) – dict containing at least one of:
    • userIds (array[int]) – user IDs to add to the project **(required if checkTeamIds absent)**
    • checkTeamIds (array[int]) – team IDs whose members will be added

Optional keyword arguments become query parameters (include, fields[…], etc.).

The endpoint’s JSON response is returned **as a UTF-8 string**.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool, ToolError
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkAddProjectPeopleTool(BaseTool):
    """Tool that wraps Teamwork’s *Add people to project* endpoint."""

    name = "teamwork_add_project_people"
    description = (
        "Add users to a Teamwork project by issuing "
        "PUT /projects/{projectId}/people.json. Provide the numeric `project_id` and a `payload` "
        "object containing `userIds` (array of user IDs) and/or `checkTeamIds` (array of team IDs). "
        "Additional keyword arguments are appended to the query string. The raw JSON response is "
        "returned as a UTF-8 string."
    )

    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "Numeric Teamwork project ID to which users will be added.",
            },
            "payload": {
                "type": "object",
                "description": (
                    "JSON body containing arrays `userIds` and/or `checkTeamIds`.\n"
                    "Example: {'userIds': [111, 222], 'checkTeamIds': [10]}"
                ),
                "properties": {
                    "userIds": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "User IDs to add to the project.",
                    },
                    "checkTeamIds": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Team IDs whose members will be added.",
                    },
                },
                "minProperties": 1,
            },
        },
        "required": ["project_id", "payload"],
        "additionalProperties": True,
    }

    def run(self, project_id: int, payload: Dict[str, Any], **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.add_project_people(project_id, payload, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            raise ToolError(f"Unexpected error: {exc}") from exc
