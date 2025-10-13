"""
Tool: TeamworkProjectDetailTool
-------------------------------

Fetch a single project from Teamwork.com with **optional advanced query
filters** (custom fields, status filters, etc.).

Internally calls :pyfunc:`aider.api.teamwork_projects.get_project_details`
and returns its JSON payload as a string.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkProjectDetailTool(BaseTool):
    """Expose Teamwork’s *Get Project* endpoint with filter support."""

    name = "teamwork_project_detail"
    description = (
        "Retrieve the complete JSON description of one Teamwork project by calling "
        "GET /projects/{projectId}.json.  Pass the numeric `project_id`; any extra keyword "
        "arguments are forwarded verbatim as query-string parameters so you can leverage "
        "Teamwork’s extensive filter set (custom fields, status filters, pagination, etc.).\n"
        "  • projectCustomField[<id>][<op>] – advanced custom-field filtering where "
        "    <op> is one of eq | not | like | not-like | lt | gt | any\n"
        "  • updatedAfter, searchTerm, reportType / reportFormat, projectType\n"
        "  • orderBy (name, duedate, lastactivity, …) together with orderMode=asc|desc\n"
        "  • pageSize & page for pagination\n"
        "  • projectStatuses, projectOwnerIds, projectIds, projectTagIds (list support)\n"
        "  • Boolean toggles such as onlyStarredProjects, includeCustomFields, includeStats …\n"
        "The tool returns the endpoint’s JSON response **as a string** so it is safe for the "
        "token counter, ready to be parsed or displayed by the LLM."
    )

    def run(self, project_id: int, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.get_project_details(project_id, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
