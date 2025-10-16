"""
Tool: TeamworkCommentTaskTool
-----------------------------

Add a **comment** to an existing Teamwork task by calling
POST /tasks/{taskId}/comments.json via :pymod:`aider.api.teamwork`.

Required parameters
-------------------
• task_id (int) – target task ID  
• payload  (object) – dict containing a `comment` object with at least a **`body`**
  field.  It may also include `notify`, `pendingFileAttachments`, etc., exactly as the
  Teamwork API expects.

Optional keyword arguments become query string parameters (eg *notify*, *getEmoji*,
*include*, *fields[users]* …).

The endpoint’s JSON response is returned **as a UTF-8 string**.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool, ToolError
from aider.api import teamwork as tw_api
from aider.api.teamwork_projects import _serialize_params
from aider.api import ApiError


class TeamworkCommentTaskTool(BaseTool):
    """Tool that wraps Teamwork’s *Create Task Comment* endpoint."""

    name = "teamwork_comment_task"
    description = (
        "Add a new comment to a Teamwork task by issuing "
        "POST /tasks/{taskId}/comments.json. Provide the numeric `task_id` and a `payload` "
        "dict whose `comment` object MUST include at least a `body` field, and may optionally "
        "include `notify`, `pendingFileAttachments`, etc. Additional keyword arguments are "
        "appended to the query string (eg `getEmoji=false`, `include=users`, "
        "`fields[comments]=id,body`). The raw JSON response is returned as a UTF-8 string."
    )

    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "integer",
                "description": "Numeric Teamwork task ID where the comment will be added",
            },
            "payload": {
                "type": "object",
                "description": (
                    "JSON body containing a `comment` object that must include at least a `body` "
                    "field and may also include `notify`, `pendingFileAttachments`, etc. "
                    "Example: {'comment': {'body': 'Looks good to me!', 'notify': [123, 456]}}"
                ),
                "properties": {
                    "comment": {
                        "type": "object",
                        "properties": {
                            "body": {"type": "string"},
                            "notify": {"type": "array", "items": {"type": "integer"}},
                            "pendingFileAttachments": {"type": "array", "items": {"type": "integer"}},
                        },
                        "required": ["body"],
                    }
                },
                "required": ["comment"],
            },
            "getEmoji": {"type": "boolean"},
            "include": {
                "type": "string",
                "description": "Comma-separated list of relations to include (users,tags,projects)",
            },
        },
        "required": ["task_id", "payload"],
        "additionalProperties": True,
    }

    def run(self, task_id: int, payload: Dict[str, Any], **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            params = _serialize_params(kwargs)
            resp = tw_api.post(f"/tasks/{task_id}/comments.json", json=payload, params=params)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            raise ToolError(f"Unexpected error: {exc}") from exc
