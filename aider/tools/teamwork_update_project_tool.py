"""
Tool: TeamworkUpdateProjectTool
-------------------------------

Update an **existing project** in Teamwork by calling
PUT /projects/{projectId}.json through
:pyfunc:`aider.api.teamwork_projects.update_project`.

Required parameters
-------------------
• project_id (int) – ID of the project to modify  
• payload    (obj) – JSON body that contains the *project* object with the
  updated fields (name, description, feature toggles, dates, tags, etc.).

Optional keyword args become query parameters (include, fields[projects], …).

The JSON response is returned **as a UTF-8 string**.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool, ToolError
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkUpdateProjectTool(BaseTool):
    """Wrap Teamwork’s *Update Project* endpoint."""

    name = "teamwork_update_project"
    description = (
        "Modify an existing Teamwork project by issuing PUT /projects/{projectId}.json. "
        "Provide `project_id` and a `payload` dict containing the `project` object with the "
        "fields to update (name, description, feature flags like `use-tasks`, start/end dates, "
        "tags, owner/company IDs, custom fields, etc.). Additional keyword arguments are forwarded "
        "as query-string parameters so you can request related objects (`include=companies`) or "
        "limit returned fields (`fields[projects]=id,name`). The raw JSON response is returned "
        "as a UTF-8 string."
    )

    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "Numeric Teamwork project ID to update",
            },
            "payload": {
                "type": "object",
                "description": "JSON body containing the *project* object",
            },
            "include": {"type": "string"},
        },
        "required": ["project_id", "payload"],
        "additionalProperties": True,
    }

    def run(self, project_id: int, payload: Dict[str, Any], **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.update_project(project_id, payload, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            raise ToolError(f"Unexpected error: {exc}") from exc
