"""
Tool: TeamworkCreateProjectTool
-------------------------------

Create a **new project** in Teamwork by calling
POST /projects.json through
:pyfunc:`aider.api.teamwork_projects.create_project`.

Required parameter
------------------
• payload (object) – top-level dict that contains the *project* object.

Optional keyword arguments become query parameters (include, fields[projects], …).

The JSON response (containing the newly created project) is returned
**as a UTF-8 string**.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool, ToolError
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkCreateProjectTool(BaseTool):
    """Wrap Teamwork’s *Create Project* endpoint."""

    name = "teamwork_create_project"
    description = (
        "Create a new project in Teamwork by issuing POST /projects.json. "
        "Provide a `payload` dict that contains the `project` object as described in the "
        "Teamwork API (name, description, feature toggles like `use-tasks`, dates, tags, "
        "owner/company IDs, custom fields, etc.). Additional keyword arguments are appended "
        "to the query string so you can request related objects (`include=companies,people`) "
        "or limit returned fields (`fields[projects]=id,name`). The raw JSON response is "
        "returned as a UTF-8 string."
    )

    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "payload": {
                "type": "object",
                "description": "JSON body containing the *project* object",
            },
            "include": {
                "type": "string",
                "description": "Comma-separated relations to embed (companies,people,customFields)",
            },
        },
        "required": ["payload"],
        "additionalProperties": True,
    }

    def run(self, payload: Dict[str, Any], **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.create_project(payload, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            raise ToolError(f"Unexpected error: {exc}") from exc
