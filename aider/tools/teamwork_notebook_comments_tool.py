"""
Tool: TeamworkNotebookCommentsTool
----------------------------------

Return the list of comments for a *single* Teamwork notebook by calling
GET /notebooks/{notebookId}/comments.json via
:pyfunc:`aider.api.teamwork_projects.notebook_comments`.

Input
-----
• notebook_id (int, required) – Teamwork notebook ID  
• Additional keyword arguments are forwarded verbatim as query parameters
  (updatedAfter, searchTerm, pagination, orderBy/orderMode, etc.).

The endpoint’s JSON response is returned **as a string** so no raw dict
is exposed to the token counter.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkNotebookCommentsTool(BaseTool):
    """Expose Teamwork’s *Get Notebook Comments* endpoint."""

    name = "teamwork_notebook_comments"
    description = (
        "List comments that belong to a single Teamwork notebook by issuing "
        "GET /notebooks/{notebookId}/comments.json. Pass the numeric `notebook_id`; all other "
        "keyword arguments are appended to the query string so you can leverage the endpoint’s "
        "rich filter set (updatedAfter, searchTerm, orderBy/orderMode, pagination, etc.). "
        "The raw JSON payload is returned as UTF-8 text."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "notebook_id": {"type": "integer", "description": "Teamwork notebook ID"},
        },
        "required": ["notebook_id"],
        "additionalProperties": True,
    }

    def run(self, notebook_id: int, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.notebook_comments(notebook_id, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
