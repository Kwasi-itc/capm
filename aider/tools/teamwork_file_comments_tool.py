"""
Tool: TeamworkFileCommentsTool
------------------------------

Return the list of comments attached to a single Teamwork file by calling
GET /files/{fileId}/comments.json via
:pyfunc:`aider.api.teamwork_projects.file_comments`.

Required parameter
------------------
• file_id (int) – Teamwork file ID

All additional keyword arguments are forwarded verbatim as query‐string
parameters (updatedAfter, searchTerm, orderBy/orderMode, pagination, …).

The endpoint’s JSON response is returned **as a UTF-8 string**.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkFileCommentsTool(BaseTool):
    """Expose Teamwork’s *Get File Comments* endpoint."""

    name = "teamwork_file_comments"
    description = (
        "List comments that belong to a single Teamwork file by issuing "
        "GET /files/{fileId}/comments.json. Provide the numeric `file_id`; any extra keyword "
        "arguments are appended to the query string so you can filter by date (`updatedAfter`), "
        "search term, order, pagination, etc. The raw JSON payload is returned as a UTF-8 string."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_id": {
                "type": "integer",
                "description": "Numeric Teamwork file ID",
            },
            "updatedAfter": {"type": "string"},
            "searchTerm": {"type": "string"},
            "orderBy": {"type": "string"},
            "orderMode": {"type": "string", "enum": ["asc", "desc"]},
            "pageSize": {"type": "integer", "minimum": 1},
            "page": {"type": "integer", "minimum": 1},
            "showDeleted": {"type": "boolean"},
        },
        "required": ["file_id"],
        "additionalProperties": True,
    }

    def run(self, file_id: int, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.file_comments(file_id, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
