"""
Tool: TeamworkProjectTasksTool
------------------------------

Return tasks for a single Teamwork project by calling
GET /projects/{projectId}/tasks.json via
``aider.api.teamwork_projects.project_tasks``.

Required positional argument
    • project_id (int) – Teamwork project ID.

Optional keyword filters (common subset)
    • updatedAfter / updatedBefore (str ISO date)
    • taskFilter="all|completed|overdue|today|thisweek" …
    • searchTerm="invoice" (str)
    • priority="high|medium|low"
    • orderBy="duedate|priority|createdat|updatedat"  +  orderMode="asc|desc"
    • pageSize, page   (ints, default 50/1)
    • showDeleted, reactions, onlyStarredProjects, skipCounts (bools)
    • projectTagIds=[...], tags=["design","ux"]  (lists)

Advanced custom-field filter
    Pass parameters like ``customField[10][eq]="Option1"`` where 10 is the
    custom-field ID and *eq* is one of eq | not | like | not-like | lt | gt | any.

The tool returns the API’s JSON response as a *string* so it is safe for the
token counter.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkProjectTasksTool(BaseTool):
    """Expose Teamwork’s *projects/{id}/tasks* endpoint."""

    name = "teamwork_project_tasks"
    description = (
        "List tasks for a single Teamwork project (specified by ``project_id``).  "
        "Supports filters such as `updatedAfter`, `taskFilter`, `searchTerm`, `priority`, "
        "`orderBy`/`orderMode`, pagination (`pageSize`, `page`), boolean flags "
        "(`showDeleted`, `onlyStarredProjects`, …) plus advanced custom-field filters "
        "using the `customField[<id>][<op>]` syntax."
    "The JSON response (``{\"tasks\": [...], \"meta\": {...}}``) is returned **as a UTF-8 string** "
    "so downstream code never sees a raw dict."
    )

    # JSON-schema for tool invocation
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "integer",
                "description": "Numeric Teamwork project ID whose tasks will be listed",
            },
        },
        "required": ["project_id"],
        "additionalProperties": True,
    }

    def run(self, project_id: int, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.project_tasks(project_id, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
