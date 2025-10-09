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

from typing import Any, Dict

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
# Projects
# --------------------------------------------------------------------------- #
def list_projects(**kwargs):
    """
    GET /projects.json - List projects visible to the authenticated user.
    """
    return _get("/projects.json", **kwargs)


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
