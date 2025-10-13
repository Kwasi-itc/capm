"""
Tool: TeamworkTaskCommentsTool
------------------------------

List *comments* attached to a specific Teamwork task by calling
GET /tasks/{taskId}/comments.json through
:pyfunc:`aider.api.teamwork_projects.task_comments`.

Required
--------
• task_id (int) – Teamwork task identifier.

Optional query parameters (all forwarded verbatim):
• updatedAfter / updatedAfterDate – ISO timestamp to fetch newer comments  
• publishedStartDate / publishedEndDate – date range filter  
• searchTerm – free-text search inside comment content  
• commentStatus – all | read | unread  
• orderBy / orderMode – date | project | user | type | all  with asc|desc  
• pageSize / page – pagination (defaults 50 / 1)  
• strictHTML, getReactionsCount – boolean flags  
• userIds, notifiedUserIds – comma-separated ID filters  
• include – reactions, users  
• fields[users] – id, firstName, lastName, avatarUrl, …  

Any other parameter documented by the API is accepted.

The endpoint’s JSON payload is returned **as a UTF-8 string** so token
counting stays consistent.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkTaskCommentsTool(BaseTool):
    """Expose Teamwork’s *Get task comments* endpoint."""

    name = "teamwork_task_comments"
    description = (
        "Fetch comments that belong to a single Teamwork task by invoking "
        "GET /tasks/{taskId}/comments.json.  Provide the numeric `task_id`; all additional "
        "keyword arguments are forwarded as query parameters, enabling the full filter set "
        "offered by Teamwork (updatedAfter, publishedStartDate/EndDate, searchTerm, "
        "commentStatus, orderBy/orderMode, pagination, include=reactions|users, "
        "fields[users], etc.).  The raw JSON response is returned as a string."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            # ----------------------------- required ----------------------------- #
            "task_id": {
                "type": "integer",
                "description": "Numeric Teamwork task ID (parent task)",
            },
            # ----------------------------- filters ------------------------------ #
            "updatedAfter": {"type": "string", "description": "ISO timestamp"},
            "updatedAfterDate": {
                "type": "string",
                "description": "DEPRECATED – use updatedAfter",
            },
            "publishedStartDate": {"type": "string", "description": "ISO date string"},
            "publishedEndDate": {"type": "string", "description": "ISO date string"},
            "searchTerm": {"type": "string", "description": "Free-text search"},
            "commentStatus": {
                "type": "string",
                "enum": ["all", "read", "unread"],
                "description": "Filter by read/unread",
            },
            # ---------------------------- ordering ------------------------------ #
            "orderBy": {
                "type": "string",
                "enum": ["all", "date", "project", "user", "type"],
                "description": "Sort column",
            },
            "orderMode": {
                "type": "string",
                "enum": ["asc", "desc"],
                "description": "Sort direction",
            },
            # --------------------------- pagination ----------------------------- #
            "pageSize": {"type": "integer", "description": "Items per page"},
            "page": {"type": "integer", "description": "Page number"},
            # ----------------------------- flags -------------------------------- #
            "strictHTML": {"type": "boolean"},
            "getReactionsCount": {"type": "boolean"},
            # ---------------------------- list filters -------------------------- #
            "userIds": {
                "type": "string",
                "description": "Comma-separated user IDs",
            },
            "notifiedUserIds": {
                "type": "string",
                "description": "Comma-separated user IDs notified",
            },
            "include": {
                "type": "string",
                "description": "Comma-separated list: reactions,users",
            },
            "fields[users]": {
                "type": "string",
                "description": "Comma-separated user field names",
            },
        },
        "required": ["task_id"],
        # Still allow any other, less-common query parameter
        "additionalProperties": True,
    }

    def run(self, task_id: int, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.task_comments(task_id, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
