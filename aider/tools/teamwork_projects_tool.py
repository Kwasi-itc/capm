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

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects


class TeamworkProjectsTool(BaseTool):
    """
    Tool that exposes Teamwork's *List Projects* endpoint.

    All keyword arguments supplied to :pymeth:`run` are forwarded as query
    parameters to :pyfunc:`aider.api.teamwork_projects.list_projects`.  See that
    function’s docstring for the exhaustive list of supported parameters.
    """

    name = "teamwork_projects"
    description = (
        "Fetch projects from Teamwork.  All keyword arguments are forwarded to "
        "`aider.api.teamwork_projects.list_projects`, so you can pass any of "
        "Teamwork’s supported list-projects query parameters (eg "
        "`searchTerm`, `pageSize`, `projectStatuses`, `onlyStarredProjects`, …)."
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
        response = tw_projects.list_projects(**kwargs)
        return response.json()
