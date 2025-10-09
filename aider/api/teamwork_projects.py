"""
aider.api.teamwork_projects
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Convenience helpers for the *Projects* endpoints of the Teamwork.com
REST API.  These thin wrappers all rely on the singleton `TeamworkClient`
instance that is created in :pyfile:`aider/api/teamwork.py`, so they pick
up authentication and domain settings automatically.

Typical usage
-------------

    from aider.api import teamwork_projects as tw_projects

    # List all active projects
    projects = tw_projects.list_projects().json()["projects"]

    # Fetch a single project
    proj = tw_projects.get_project(12345).json()["project"]

    # Create a project
    new_proj = tw_projects.create_project(
        {
            "name": "New Website",
            "description": "Re-build the public site",
        }
    ).json()["project"]
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .teamwork import delete as _delete
from .teamwork import get as _get
from .teamwork import patch as _patch
from .teamwork import post as _post
from .teamwork import put as _put

__all__ = [
    "list_projects",
    "get_project",
    "create_project",
    "update_project",
    "delete_project",
]


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _serialize_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert *params* to the format expected by the Teamwork API:

    • ``list``/``tuple``/``set`` values are joined by commas  
    • ``bool`` values are lower-cased strings ("true"/"false")

    The original dict is **not** modified; a new one is returned.
    """
    out: Dict[str, Any] = {}
    for key, val in params.items():
        if isinstance(val, (list, tuple, set)):
            out[key] = ",".join(str(x) for x in val)
        elif isinstance(val, bool):
            out[key] = str(val).lower()
        else:
            out[key] = val
    return out


# --------------------------------------------------------------------------- #
# Projects
# --------------------------------------------------------------------------- #
def list_projects(query: Optional[Dict[str, Any]] = None, **query_params):
    """
    GET /projects/api/v3/projects.json - List projects visible to the authenticated user.

    Parameters
    ----------
    query:
        Optional explicit dict of query parameters.
    **query_params:
        Additional query parameters passed as keyword arguments.

    Examples
    --------
        # basic call
        list_projects()

        # with explicit parameters
        list_projects(searchTerm="Website", pageSize=100)

        # with list parameters
        list_projects(projectStatuses=["active", "late"], onlyStarredProjects=True)
    """
    params = {**(query or {}), **query_params}
    return _get("/projects/api/v3/projects.json", params=_serialize_params(params))


def get_project(project_id: int | str, **kwargs):
    """
    GET /projects/{id}.json - Retrieve a single project by *project_id*.
    """
    return _get(f"/projects/{project_id}.json", **kwargs)


def create_project(data: Dict[str, Any], **kwargs):
    """
    POST /projects.json - Create a new project.

    The *data* dict should contain the fields expected by Teamwork,
    eg: ``{"name": "Site redesign", "description": "...", ...}``.
    """
    return _post("/projects.json", json=data, **kwargs)


def update_project(project_id: int | str, data: Dict[str, Any], **kwargs):
    """
    PUT /projects/{id}.json - Update an existing project.
    """
    return _put(f"/projects/{project_id}.json", json=data, **kwargs)


def delete_project(project_id: int | str, **kwargs):
    """
    DELETE /projects/{id}.json - Delete (or archive) a project.
    """
    return _delete(f"/projects/{project_id}.json", **kwargs)
