"""
Tool: TeamworkProjectsTool
--------------------------

Provides the *teamwork_projects* tool that fetches projects from
Teamwork.com by calling :pyfunc:`aider.api.teamwork_projects.list_projects`.

The returned value is the JSON-decoded response body, so it can be used
directly inside other tools or printed for the user.

Typical usage inside the aider CLI::

    !teamwork_projects                         # list projects with defaults
    !teamwork_projects searchTerm="Website"    # with query params
"""
from __future__ import annotations

from typing import Any, Dict
import json

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkProjectsTool(BaseTool):
    """
    Tool that exposes Teamwork's *List Projects* endpoint.

    All keyword arguments supplied to :pymeth:`run` are forwarded as query
    parameters to :pyfunc:`aider.api.teamwork_projects.list_projects`.  See that
    function’s docstring for the exhaustive list of supported parameters.
    """

    name = "teamwork_projects"
    description = (
        "List projects the authenticated Teamwork user can access by calling "
        "GET /projects.json.  All keyword arguments you pass are forwarded as query-string "
        "parameters to Teamwork’s List-Projects endpoint, and the raw JSON response is "
        "returned as a string.  "
        "Common parameters include:\n"
        "  • searchTerm (str) – filter by project name\n"
        "  • pageSize (int) – items per page (default 50)\n"
        "  • page (int) – page number (default 1)\n"
        "  • projectStatuses (list[str]) – active | current | late | upcoming | completed | deleted\n"
        "  • projectType (str) – filter by project type\n"
        "  • orderBy (str) – name, duedate, companyname, etc.\n"
        "  • orderMode (str) – asc | desc\n"
        "  • onlyStarredProjects (bool)\n"
        "  • includeStats / includeProjectUserInfo (bool)\n"
        "and any other parameter accepted by the API."
    )

    def run(self, **kwargs: Dict[str, Any]):  # noqa: D401
        """
        Execute the tool.

        Parameters
        ----------
        **kwargs
            Any query parameters accepted by Teamwork’s *List Projects* API,
            eg: ``searchTerm="Website", pageSize=100``.
        """
        try:
            response = tw_projects.list_projects(**kwargs)
            # Always return a *string* so upstream token counting never sees a dict.
            return json.dumps(response.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
