"""
Tool: TeamworkGetCurrentUserTool
--------------------------------

Fetch **details of the currently authenticated user** in Teamwork by calling
GET /me.json through
:pyfunc:`aider.api.teamwork_users.get_current_user`.

Optional keyword arguments map 1-to-1 to the documented query flags
(`getPreferences`, `fullProfile`, …).  The JSON response is returned
**as a UTF-8 string**.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool, ToolError
from aider.api import teamwork_users as tw_users
from aider.api import ApiError


class TeamworkGetCurrentUserTool(BaseTool):
    """Wrap Teamwork’s *Get Current User Details* endpoint."""

    name = "teamwork_get_current_user"
    description = (
        "Return details of the signed-in Teamwork user by issuing GET /me.json. "
        "You may pass any of the documented boolean query flags (getPreferences, "
        "fullProfile, getDefaultFilters, sharedFilter, getAccounts, includeAuth) "
        "to control the response.  The raw JSON response is returned as a UTF-8 string."
    )

    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "getPreferences": {
                "type": "boolean",
                "description": "Include user preferences (ordering of comments, etc.)",
            },
            "fullProfile": {
                "type": "boolean",
                "description": "Include additional profile details",
            },
            "getDefaultFilters": {
                "type": "boolean",
                "description": "Include the user's default filters",
            },
            "sharedFilter": {
                "type": "boolean",
                "description": "Include shared filters",
            },
            "getAccounts": {
                "type": "boolean",
                "description": "Include accounts information",
            },
            "includeAuth": {
                "type": "boolean",
                "description": "Include the API key – be careful sharing this data!",
            },
        },
        "required": [],
        "additionalProperties": False,
    }

    def run(self, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_users.get_current_user(**kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            raise ToolError(f"Unexpected error: {exc}") from exc
