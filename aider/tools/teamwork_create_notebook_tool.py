"""
Tool: TeamworkCreateNotebookTool
--------------------------------

Create a **new notebook** within an existing Teamwork project by calling
POST /projects/{projectId}/notebooks.json through
:pyfunc:`aider.api.teamwork_projects.create_notebook`.

Required parameters
-------------------
• project_id (int) – target project ID  
• payload     (object) – dict containing a `notebook` object with at least `name`, `description`, and `contents` fields. It may additionally include `categoryId`, `isFullWidth`, `isPrivate`, `locked`, `newVersion`, and `notify`.

Optional keyword arguments become query parameters (getEmoji, include,
fields[users], fields[tags], …).

The endpoint’s JSON response is returned **as a UTF-8 string**.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool, ToolError
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkCreateNotebookTool(BaseTool):
    """Tool that wraps Teamwork’s *Create Notebook* endpoint."""

    name = "teamwork_create_notebook"
    description = (
        "Create a new notebook inside a Teamwork project by issuing "
        "POST /projects/{projectId}/notebooks.json. Provide the numeric `project_id` and a "
        "`payload` dict whose `notebook` object MUST include at least a `name`, `description`, and `contents` field, and may optionally include `categoryId`, `isFullWidth`, `isPrivate`, `locked`, `newVersion`, and `notify` "
        "field as expected by Teamwork. Additional keyword arguments are appended to the query "
        "string, allowing emoji parsing (`getEmoji=false`), inclusion of related objects "
        "(`include=projects,tags`), or field selection via `fields[notebooks]=id,name`. The raw "
        "JSON response is returned as a UTF-8 string."
    )

    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "Numeric Teamwork project ID where the notebook will be created",
            },
            "payload": {
                "type": "object",
                "description": (
                    "JSON body containing a `notebook` object that must include at least "
                    "`name`, `description`, and `contents` fields, and may also include `categoryId`, "
                    "`isFullWidth`, `isPrivate`, `locked`, `newVersion`, and `notify`. "
                    "Example: {'notebook': {'name': 'Sprint Retro', 'description': 'Notes…', "
                    "'contents': '# Retrospective\\n…', 'categoryId': 1234}}"
                ),
                "properties": {
                    "notebook": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "categoryId": {"type": "integer"},
                            "contents": {"type": "string"},
                            "isFullWidth": {"type": "boolean"},
                            "isPrivate": {"type": "boolean"},
                            "locked": {"type": "boolean"},
                            "newVersion": {"type": "boolean"},
                            "notify": {"type": "object"},
                        },
                        "required": ["name", "description", "contents"],
                    }
                },
                "required": ["notebook"],
            },
            "getEmoji": {"type": "boolean"},
            "include": {
                "type": "string",
                "description": "Comma-separated list of relations to include "
                "(projects,tags,users,notebookCategories,companies,teams)",
            },
        },
        "required": ["project_id", "payload"],
        "additionalProperties": True,
    }

    def run(self, project_id: int, payload: Dict[str, Any], **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.create_notebook(project_id, payload, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            raise ToolError(f"Unexpected error: {exc}") from exc
