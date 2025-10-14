"""
Tool: TeamworkNotebookDetailTool
--------------------------------

Retrieve a single notebook from Teamwork.com by calling
GET /notebooks/{notebookId}.json through
:pyfunc:`aider.api.teamwork_projects.get_notebook`.

All query parameters accepted by the endpoint – updatedAfter, projectType,
showDeleted, include, field selectors, etc. – can be passed as keyword
arguments. The JSON response body is returned **as a UTF-8 string** to
avoid leaking a raw Python dict to the language model.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkNotebookDetailTool(BaseTool):
    """Expose Teamwork’s *Get Notebook* endpoint."""

    name = "teamwork_notebook_detail"
    description = (
        "Return the full JSON representation of a single Teamwork notebook by issuing "
        "GET /notebooks/{notebookId}.json. Provide the numeric `notebook_id`; any additional "
        "keyword arguments are appended to the query string so you can request extra relations "
        "(`include=projects,tags,users`), restrict returned fields (`fields[users]=id,name`), "
        "filter by project type or last update date, show deleted notebooks, etc. "
        "The raw response is returned as a UTF-8 JSON string."
    )

    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "notebook_id": {
                "type": "integer",
                "description": "Numeric Teamwork notebook ID to retrieve",
            },
            "updatedAfter": {"type": "string"},
            "projectType": {
                "type": "string",
                "enum": ["normal", "tasklists-template", "projects-template"],
            },
            "showDeleted": {"type": "boolean"},
            "include": {
                "type": "string",
                "description": "Comma-separated list of relations to include "
                "(projects,tags,users,notebookCategories,companies,teams)",
            },
        },
        "required": ["notebook_id"],
        "additionalProperties": True,
    }

    def run(self, notebook_id: int, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.get_notebook(notebook_id, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
