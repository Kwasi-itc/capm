"""
Tool: TeamworkUpdateNotebookTool
--------------------------------

Edit the attributes of an existing Teamwork notebook by calling
PATCH /notebooks/{notebookId}.json through
:pyfunc:`aider.api.teamwork_projects.update_notebook`.

Input
-----
• notebook_id (int, required) – target notebook ID  
• payload (object, required) – JSON body with the fields to update  
• Optional keyword arguments become query parameters (getEmoji, include,
  fields[users], fields[projects], …).

The endpoint’s JSON response is returned **as a UTF-8 string**.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool, ToolError
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkUpdateNotebookTool(BaseTool):
    """Tool that wraps Teamwork’s *Edit Notebook* endpoint."""

    name = "teamwork_update_notebook"
    description = (
        "Modify an existing Teamwork notebook by issuing "
        "PATCH /notebooks/{notebookId}.json. Provide the numeric `notebook_id` and a `payload` "
        "object with the fields to change (name, description, isPrivate, locked, …). "
        "Additional keyword arguments are appended to the query string so you can request emoji "
        "parsing (`getEmoji=false`), include related objects (`include=projects,tags`), or limit "
        "returned fields via `fields[notebooks]=id,name`. The raw JSON payload is returned as a "
        "UTF-8 string."
    )

    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "notebook_id": {
                "type": "integer",
                "description": "Numeric Teamwork notebook ID to update",
            },
            "payload": {
                "type": "object",
                "description": "JSON body containing the fields to modify",
            },
            "getEmoji": {"type": "boolean"},
            "include": {
                "type": "string",
                "description": "Comma-separated list of relations to include "
                "(projects,tags,users,notebookCategories,companies,teams)",
            },
        },
        "required": ["notebook_id", "payload"],
        "additionalProperties": True,
    }

    def run(self, notebook_id: int, payload: Dict[str, Any], **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.update_notebook(notebook_id, payload, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            raise ToolError(f"Unexpected error: {exc}") from exc
