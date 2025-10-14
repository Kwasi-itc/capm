"""
Tool: TeamworkDeleteNotebookTool
--------------------------------

Delete an existing Teamwork notebook by calling
DELETE /notebooks/{notebookId}.json through
:pyfunc:`aider.api.teamwork_projects.delete_notebook`.

Safety-first: the tool requires an explicit ``confirm=true`` argument
before it will execute the destructive call.  If the confirmation flag
is omitted or ``false`` the tool responds with an explanatory message
and **does not** perform the deletion.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool, ToolError
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkDeleteNotebookTool(BaseTool):
    """Tool that deletes a Teamwork notebook after explicit confirmation."""

    name = "teamwork_delete_notebook"
    description = (
        "Permanently delete a notebook in Teamwork by issuing "
        "DELETE /notebooks/{notebookId}.json. Supply the numeric `notebook_id`. "
        "Safety guard: pass confirm=true to skip the interactive yes/no prompt; "
        "otherwise the tool asks for confirmation in the console before proceeding. "
        "On success it returns {\"status\": \"deleted\", \"notebook_id\": <id>} or "
        "relays the API’s JSON error body."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "notebook_id": {"type": "integer", "description": "Numeric Teamwork notebook ID"},
            "confirm": {
                "type": "boolean",
                "description": "Must be true to actually delete the notebook",
                "default": False,
            },
        },
        "required": ["notebook_id"],
        "additionalProperties": True,
    }

    def run(self, notebook_id: int, confirm: bool = False, **kwargs: Dict[str, Any]):  # noqa: D401
        # ------------------------------------------------------------------
        # Interactive safeguard
        # ------------------------------------------------------------------
        if not confirm:
            answer = input(
                f"Are you sure you want to DELETE notebook {notebook_id}? [y/N]: "
            ).strip().lower()
            if answer not in ("y", "yes"):
                return "Deletion cancelled."

        try:
            resp = tw_projects.delete_notebook(notebook_id, **kwargs)
            # Teamwork returns 204 No Content → fabricate a tiny JSON payload
            if resp.status_code == 204 or not resp.content:
                return json.dumps({"status": "deleted", "notebook_id": notebook_id}, ensure_ascii=False)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            raise ToolError(f"Unexpected error during deletion: {exc}") from exc
