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
        "List projects that are visible to the authenticated Teamwork user.  Every keyword "
        "argument you provide is forwarded as a query-string parameter to Teamwork’s *List "
        "Projects* endpoint, so you can use the full range of filters such as "
        "`searchTerm=\"Website\"`, `pageSize=100`, `projectStatuses=[\"active\",\"late\"]`, "
        "`onlyStarredProjects=True`, etc."
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
