"""
Tool: TeamworkNotebookVersionsTool
----------------------------------

Return the list of saved versions for a single Teamwork notebook by calling
GET /notebooks/{notebookId}/versions.json via
:pyfunc:`aider.api.teamwork_projects.notebook_versions`.

Input
-----
• notebook_id (int, required) – Teamwork notebook ID  
• Optional keyword arguments become query parameters (include, fields[users], …).

The endpoint’s JSON response is returned **as a UTF-8 string**.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkNotebookVersionsTool(BaseTool):
    """Expose Teamwork’s *Get Notebook Versions* endpoint."""

    name = "teamwork_notebook_versions"
    description = (
        "List every saved version of a single Teamwork notebook by issuing "
        "GET /notebooks/{notebookId}/versions.json. Provide the numeric `notebook_id`; "
        "any additional keyword arguments are forwarded as query-string parameters – for example "
        "`include=users` to embed author details or `fields[users]=id,name` to limit user fields. "
        "The raw JSON payload is returned as a UTF-8 string."
    )

    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "notebook_id": {
                "type": "integer",
                "description": "Numeric Teamwork notebook ID",
            },
            "include": {
                "type": "string",
                "description": "Comma-separated list of relations to include (users)",
            },
        },
        "required": ["notebook_id"],
        "additionalProperties": True,
    }

    def run(self, notebook_id: int, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.notebook_versions(notebook_id, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
