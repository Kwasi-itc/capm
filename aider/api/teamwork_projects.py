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
    "get_project_details",
    "create_project",
    "update_project",
    "delete_project",
    "active_projects_metrics",
    "health_projects_metrics",
    "owners_projects_metrics",
    "list_project_updates",
    "project_updates",
    "project_tasks",
    "project_tasklists",
    "list_tasklists",
    "list_tasks",
    "get_task",
    "tasklist_tasks",
    "create_task",
    "get_tasklist",
    "list_project_categories",
    "completed_tasks_metrics",
    "late_tasks_metrics",
    "user_task_completion",
    "task_subtasks",
    "create_subtask",
    "delete_task",
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
    GET /projects.json - List projects visible to the authenticated user.

    Any of the query-string parameters supported by Teamwork’s “List
    Projects” endpoint can be supplied either via the *query* dict or as
    keyword arguments.  Below is the most commonly used subset (see the
    official docs for the exhaustive list):

    =======================================================================
    updatedAfter                     str   – return projects updated > date
    timeMode                         str   – ``timelogs`` | ``estimated``
    searchTerm                       str   – filter by project name
    reportType                       str   – ``project`` | ``health`` (def: project)
    reportTimezone                   str   – timezone for report dates
    reportFormat                     str   – ``csv`` | ``html`` | ``pdf`` | ``xls``
    projectType                      str   – restrict to project type
    orderMode                        str   – ``asc`` | ``desc`` (def: asc)
    orderBy                          str   – ``name`` | ``duedate`` | … (def: name)
    pageSize                         int   – items per page   (def: 50)
    page                             int   – page number      (def: 1)
    onlyStarredProjects              bool  – starred only
    onlyArchivedProjects             bool  – archived only
    projectStatuses                  list  – eg ``["active","late"]``
    projectIds                       list  – restrict to specific IDs
    includeStats                     bool  – include status counts
    includeProjectUserInfo           bool  – include user-specific data
    =======================================================================

    Examples
    --------
        # basic call
        list_projects()

        # with explicit parameters
        list_projects(searchTerm="Website", pageSize=100)

        # with list parameters
        list_projects(projectStatuses=["active", "late"], onlyStarredProjects=True)

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
    return _get("/projects.json", params=_serialize_params(params))


def get_project(
    project_id: int | str,
    *,
    query: Optional[Dict[str, Any]] = None,
    **query_params,
):
    """
    GET /projects/{id}.json – Retrieve a single project.

    Parameters
    ----------
    project_id:
        The numeric ID of the project.
    query / **query_params:
        Optional query-string parameters (see get_project_details for list).
    """
    params = {**(query or {}), **query_params}
    return _get(f"/projects/{project_id}.json", params=_serialize_params(params))


def get_project_details(
    project_id: int | str,
    *,
    query: Optional[Dict[str, Any]] = None,
    **query_params,
):
    """
    GET /projects/{id}.json – Retrieve a project with optional **advanced filters**.

    Supports every parameter accepted by Teamwork’s “Get a project” endpoint,
    including custom-field filters using the ``projectCustomField[id][op]`` syntax.

    Examples
    --------
        # plain request
        get_project_details(123)

        # filter by custom field id 10 equals "Option1"
        get_project_details(123, **{"projectCustomField[10][eq]": "Option1"})

        # pass arbitrary query parameters
        get_project_details(123, orderMode="asc", includeCustomFields=True)
    """
    params = {**(query or {}), **query_params}
    return _get(f"/projects/{project_id}.json", params=_serialize_params(params))


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


def active_projects_metrics(**kwargs):
    """
    GET /projects/metrics/active.json – Return metrics about active
    projects, including the total count.

    Returns
    -------
    requests.Response
        The JSON body looks like ``{"count": <int>, ...}``.
    """
    return _get("/projects/metrics/active.json", **kwargs)


def completed_tasks_metrics(**kwargs):
    """
    GET /tasks/metrics/complete.json – Return the total number of completed
    tasks visible to the authenticated user.

    Returns
    -------
    requests.Response
        JSON body like ``{"count": <int>}``.
    """
    return _get("/tasks/metrics/complete.json", **kwargs)


def late_tasks_metrics(**kwargs):
    """
    GET /tasks/metrics/late.json – Return the total number of *late* tasks
    that the authenticated user can access.

    Returns
    -------
    requests.Response
        JSON body shaped like ``{"count": <int>}``.
    """
    return _get("/tasks/metrics/late.json", **kwargs)


# --------------------------------------------------------------------------- #
# User task‐completion report
# --------------------------------------------------------------------------- #
def user_task_completion(
    user_id: int | str,
    *,
    query: Optional[Dict[str, Any]] = None,
    **query_params,
):
    """
    GET /reporting/precanned/usertaskcompletion/{userId}.json – Retrieve task
    completion statistics for a *single* user (person).

    Any query parameter accepted by Teamwork’s endpoint may be supplied either
    via the *query* dict or as keyword arguments.  This includes:

    • userType              – account | collaborator | contact  
    • updatedAfter          – ISO date/time string  
    • startDate / endDate   – date range for the report  
    • searchTerm            – filter by comment content  
    • orderBy / orderMode   – name, id, completedtasks … with asc|desc  
    • pagination & flags    – pageSize, page, skipCounts, showDeleted, …  
    • list filters          – teamIds, projectIds, jobRoleIds, ids, …  
    • include / fields[…] selectors

    Examples
    --------
        user_task_completion(42)
        user_task_completion(42, startDate="2025-01-01", endDate="2025-06-30")
        user_task_completion(42, **{"fields[person]": "id,firstName,lastName"})

    Returns
    -------
    requests.Response
        JSON payload containing the person object and completion stats.
    """
    params = {**(query or {}), **query_params}
    return _get(
        f"/reporting/precanned/usertaskcompletion/{user_id}.json",
        params=_serialize_params(params),
    )


def health_projects_metrics(query: Optional[Dict[str, Any]] = None, **query_params):
    """
    GET /projects/metrics/healths.json – Return the number of projects in each
    health category *visible to the authenticated user*.

    All filters accepted by the endpoint (``projectStatus``, ``onlyStarredProjects``,
    ``projectTagIds`` … see Teamwork docs) can be supplied either via the *query*
    dict or as keyword arguments.

    Returns
    -------
    requests.Response
        JSON body such as ``{"good": 12, "ok": 7, "bad": 2, "not_set": 3}``.
    """
    params = {**(query or {}), **query_params}
    return _get("/projects/metrics/healths.json", params=_serialize_params(params))


def owners_projects_metrics(query: Optional[Dict[str, Any]] = None, **query_params):
    """
    GET /projects/metrics/owners.json – Count projects per *project owner user*,
    including a bucket for un-assigned projects.

    Any query-string filter supported by the endpoint can be provided either
    via the *query* dict or as keyword arguments.  Common parameters include:

    • orderMode (str) – ``asc`` | ``desc`` (default ``desc``)  
    • pageSize (int) – items per page (default 50)  
    • page (int) – page number (default 1)  
    • skipCounts (bool) – performance hint  
    • onlyStarredProjects (bool)  
    • matchAllProjectTags (bool)  
    • projectTagIds (list[int])  
    • projectStatuses (list[str]) – active | current | late | upcoming | completed | deleted  
    • projectOwnerIds / projectIds / projectHealths / projectCompanyIds / projectCategoryIds …

    Returns
    -------
    requests.Response
        JSON body like ``{"owners": [{"userId": 123, "count": 7}, …], "unassigned": 3}``
    """
    params = {**(query or {}), **query_params}
    return _get("/projects/metrics/owners.json", params=_serialize_params(params))


# --------------------------------------------------------------------------- #
# Project updates
# --------------------------------------------------------------------------- #
def list_project_updates(query: Optional[Dict[str, Any]] = None, **query_params):
    """
    GET /projects/updates.json – Return project-update messages from every
    project the authenticated user can access.

    Any query-string filter documented for the endpoint may be supplied, e.g.:

    • updatedAfter, createdAfter (str ISO date)  
    • projectStatus (str) – active | current | late | upcoming | completed | deleted  
    • orderBy ('date' | 'color' | 'health' | 'project' | 'user') with orderMode asc|desc  
    • projectId (int) – restrict to a single project  
    • pageSize (int, default 50), page (int, default 1)  
    • Boolean flags such as skipCounts, showDeleted, reactions, onlyStarredProjects, etc.  
    • list filters: projectTagIds, projectStatuses, projectOwnerIds, projectIds, projectHealths…

    Returns
    -------
    requests.Response
        JSON payload containing the list of updates.
    """
    params = {**(query or {}), **query_params}
    return _get("/projects/updates.json", params=_serialize_params(params))


def project_updates(
    project_id: int | str,
    *,
    query: Optional[Dict[str, Any]] = None,
    **query_params,
):
    """
    GET /projects/{projectId}/updates.json – Return status‐updates that belong
    to a *single* project.

    All query-string filters supported by the generic updates endpoint are
    available here as well (``updatedAfter``, ``orderBy``, pagination,
    ``showDeleted``, etc.).

    Parameters
    ----------
    project_id:
        Numeric Teamwork project ID.
    query / **query_params:
        Optional query parameters (see Teamwork docs).

    Returns
    -------
    requests.Response
        JSON list of update objects.
    """
    params = {**(query or {}), **query_params}
    return _get(f"/projects/{project_id}/updates.json", params=_serialize_params(params))


# --------------------------------------------------------------------------- #
# Project tasks
# --------------------------------------------------------------------------- #
def project_tasks(
    project_id: int | str,
    *,
    query: Optional[Dict[str, Any]] = None,
    **query_params,
):
    """
    GET /projects/{projectId}/tasks.json – List tasks that belong to *one*
    project.

    Parameters (subset)
    -------------------
    updatedAfter / updatedBefore   str   – filter by last-update date
    taskFilter                     str   – ``all``, ``completed``, ``overdue``, …
    searchTerm                     str   – free-text search
    priority                       str   – ``low`` | ``medium`` | ``high`` | …
    orderBy                        str   – ``duedate`` | ``priority`` | ``createdat`` …
    orderMode                      str   – ``asc`` | ``desc`` (default asc)
    pageSize / page                int   – pagination (defaults 50 / 1)
    showDeleted / skipCounts       bool
    onlyStarredProjects            bool
    projectTagIds, tags            list[int] / list[str]
    customField[ID][op]            str   – advanced custom-field filter,
                                           where *op* = eq | not | like | gt | lt | any

    All additional query parameters accepted by Teamwork may be supplied
    via *query* or **query_params.

    Returns
    -------
    requests.Response
        Body shape: ``{"tasks": [...], "meta": {...}}``.
    """
    params = {**(query or {}), **query_params}
    return _get(f"/projects/{project_id}/tasks.json", params=_serialize_params(params))


# --------------------------------------------------------------------------- #
# Project tasklists
# --------------------------------------------------------------------------- #
def project_tasklists(
    project_id: int | str,
    *,
    query: Optional[Dict[str, Any]] = None,
    **query_params,
):
    """
    GET /projects/{projectId}/tasklists.json – List task-lists that belong to a
    single project.

    Any query parameter accepted by Teamwork’s “Get tasklists in a project”
    endpoint can be supplied via *query* or **query_params, for example:

    • updatedAfter (str ISO) – filter by last update date  
    • searchTerm (str) – free-text search  
    • orderMode (“asc” | “desc”), orderBy (“displayorder”, “name”, …)  
    • pagination: pageSize (int, default 50), page (int, default 1)  
    • showPrivate / showDeleted / showCompleted / completedOnly (bool flags)  
    • include (list[str]) – eg “defaultTasks”, “companies”, “milestones”…  
    • ids / projectIds / projectCompanyIds (list[int]) – filtering by IDs  
    • fields[tasklists] / fields[users] / … – field selection

    Returns
    -------
    requests.Response
        JSON body like ``{"tasklists": [...], "meta": {...}}``.
    """
    params = {**(query or {}), **query_params}
    return _get(f"/projects/{project_id}/tasklists.json", params=_serialize_params(params))


# --------------------------------------------------------------------------- #
# Task-lists across *all* projects
# --------------------------------------------------------------------------- #
def list_tasklists(query: Optional[Dict[str, Any]] = None, **query_params):
    """
    GET /tasklists.json – Return task-lists visible to the authenticated user
    across *all* projects.

    This supports the exact same query-string parameters as the per-project
    endpoint (``updatedAfter``, ``searchTerm``, ``orderMode``, ``pageSize``,
    flags such as ``showPrivate`` / ``completedOnly`` / ``skipCounts``, list
    filters like ``projectIds`` / ``ids`` / ``include`` and all the
    ``fields[...]`` selectors).

    Parameters
    ----------
    query:
        Optional dict with query parameters.
    **query_params:
        Additional query parameters as keyword arguments.

    Returns
    -------
    requests.Response
        JSON body shaped like ``{"tasklists": [...], "meta": {...}}``.
    """
    params = {**(query or {}), **query_params}
    return _get("/tasklists.json", params=_serialize_params(params))


# --------------------------------------------------------------------------- #
# Tasks across *all* projects
# --------------------------------------------------------------------------- #
def list_tasks(query: Optional[Dict[str, Any]] = None, **query_params):
    """
    GET /tasks.json – Return tasks visible to the authenticated user across all
    projects and task-lists.

    This endpoint supports the **very large** set of query parameters offered by
    Teamwork’s *Get all tasks* API, including but not limited to:

    • Date filters – updatedAfter/Before, dueAfter/Before, createdAfter/Before …  
    • taskFilter presets – ``all``, ``overdue``, ``today`` …  
    • searchTerm, priority, orderBy & orderMode, pagination (pageSize/page)  
    • Boolean flags – showDeleted, onlyUnplanned, completedOnly, skipCounts, …  
    • List filters – tags, tagIds, tasklistIds, projectIds, projectStatuses, …  
    • Advanced custom field filter syntax: ``customField[10][eq]=Option1``

    Parameters
    ----------
    query:
        Optional dictionary containing query parameters.
    **query_params:
        Additional query parameters passed as keyword arguments.

    Returns
    -------
    requests.Response
        JSON body shaped like ``{"tasks": [...], "meta": {...}}``.
    """
    params = {**(query or {}), **query_params}
    return _get("/tasks.json", params=_serialize_params(params))


# --------------------------------------------------------------------------- #
# Single task
# --------------------------------------------------------------------------- #
def get_task(
    task_id: int | str,
    *,
    query: Optional[Dict[str, Any]] = None,
    **query_params,
):
    """
    GET /tasks/{taskId}.json – Retrieve one specific task.

    All query parameters accepted by Teamwork’s *Get a task* endpoint can be
    supplied either via the *query* dict or as keyword arguments.
    This includes advanced custom-field filters in the form
    ``customField[id][op]=value`` where *op* is one of
    like | not-like | eq | not | lt | gt | any.

    Examples
    --------
        # basic request
        get_task(987654)

        # filter by custom field id 10 equals "Option1"
        get_task(987654, **{"customField[10][eq]": "Option1"})
    """
    params = {**(query or {}), **query_params}
    return _get(f"/tasks/{task_id}.json", params=_serialize_params(params))


# --------------------------------------------------------------------------- #
# Single task-list
# --------------------------------------------------------------------------- #
def get_tasklist(
    tasklist_id: int | str,
    *,
    query: Optional[Dict[str, Any]] = None,
    **query_params,
):
    """
    GET /tasklists/{tasklistId}.json – Retrieve one specific task-list.

    Supports the full range of query parameters accepted by the list endpoints
    (updatedAfter, include lists, fields[...], showPrivate/deleted/completed,
    pagination, etc.).

    Parameters
    ----------
    tasklist_id:
        Teamwork task-list ID.
    query / **query_params:
        Optional query-string filters.

    Returns
    -------
    requests.Response
        The JSON payload looks like ``{"tasklist": {...}}``.
    """
    params = {**(query or {}), **query_params}
    return _get(f"/tasklists/{tasklist_id}.json", params=_serialize_params(params))


# --------------------------------------------------------------------------- #
# Task-list tasks
# --------------------------------------------------------------------------- #
def task_subtasks(
    task_id: int | str,
    *,
    query: Optional[Dict[str, Any]] = None,
    **query_params,
):
    """
    GET /tasks/{taskId}/subtasks.json – List *sub-tasks* that belong to the
    specified parent task.

    The endpoint accepts the **same rich filter set** as the generic list-tasks
    API, including advanced custom-field filters using the
    ``customField[id][op]=value`` pattern where *op* = like | not-like | eq |
    not | lt | gt | any.

    Examples
    --------
        # list every sub-task
        task_subtasks(987654)

        # only completed sub-tasks updated after a date
        task_subtasks(
            987654,
            taskFilter="completed",
            updatedAfter="2025-01-01",
            **{"customField[10][eq]": "Option1"},
        )

    Parameters
    ----------
    task_id:
        Numeric Teamwork parent task ID.
    query / **query_params:
        Optional query parameters documented by Teamwork.

    Returns
    -------
    requests.Response
        JSON payload shaped like ``{"tasks": [...], "meta": {...}}``.
    """
    params = {**(query or {}), **query_params}
    return _get(f"/tasks/{task_id}/subtasks.json", params=_serialize_params(params))


def tasklist_tasks(
    tasklist_id: int | str,
    *,
    query: Optional[Dict[str, Any]] = None,
    **query_params,
):
    """
    GET /tasklists/{tasklistId}/tasks.json – List tasks that belong to *one*
    task-list.

    Accepts the full range of filters documented by Teamwork’s “Get a specific
    task-list’s tasks” endpoint, including custom-field filters with the
    ``customField[id][op]=value`` syntax, taskFilter presets, date ranges,
    pagination, flags such as showDeleted / onlyUnplanned / matchAllTags, etc.

    Parameters
    ----------
    tasklist_id:
        Numeric Teamwork task-list ID.
    query / **query_params:
        Optional query-string parameters.

    Returns
    -------
    requests.Response
        JSON body shaped like ``{"tasks": [...], "meta": {...}}``.
    """
    params = {**(query or {}), **query_params}
    return _get(f"/tasklists/{tasklist_id}/tasks.json", params=_serialize_params(params))


# --------------------------------------------------------------------------- #
# Create task in a task-list
# --------------------------------------------------------------------------- #
def create_task(
    tasklist_id: int | str,
    data: Dict[str, Any],
    **kwargs,
):
    """
    POST /tasklists/{tasklistId}/tasks.json – Create a *new* task in the
    specified task-list.

    The JSON *data* payload can contain any keys allowed by the Teamwork
    endpoint such as ``task``, ``tags``, ``attachments``, ``taskOptions``,
    ``card``, ``workflows``…  For example::

        create_task(
            987654,
            {
                "task": {
                    "name": "Write release notes",
                    "description": "Draft for v1.4",
                    "startDate": "2025-10-01",
                    "dueDate": "2025-10-05",
                },
                "tags": [{"name": "documentation"}],
            }
        )

    Parameters
    ----------
    tasklist_id:
        Numeric Teamwork task-list ID that will hold the new task.
    data:
        Dict representing the JSON body to send.
    **kwargs:
        Extra arguments forwarded to :pyfunc:`requests.post`.

    Returns
    -------
    requests.Response
        JSON payload with the newly created task object.
    """
    return _post(f"/tasklists/{tasklist_id}/tasks.json", json=data, **kwargs)


# --------------------------------------------------------------------------- #
# Create sub-task under a parent task
# --------------------------------------------------------------------------- #
def create_subtask(
    task_id: int | str,
    data: Dict[str, Any],
    **kwargs,
):
    """
    POST /tasks/{taskId}/subtasks.json – Create a *new* sub-task beneath the
    given parent task.

    The JSON *data* body supports the same structure as the generic
    create-task endpoint (``task``, ``tags``, ``attachments``, ``taskOptions``,
    ``card``, ``workflows`` …).

    Example
    -------
        create_subtask(
            112233,
            {
                "task": {
                    "name": "Write unit tests",
                    "description": "Cover edge-cases",
                    "dueDate": "2025-11-01",
                },
                "tags": [{"name": "testing"}],
            }
        )
    """
    return _post(f"/tasks/{task_id}/subtasks.json", json=data, **kwargs)


# --------------------------------------------------------------------------- #
# Delete task
# --------------------------------------------------------------------------- #
def delete_task(task_id: int | str, **kwargs):
    """
    DELETE /tasks/{taskId}.json – Delete an existing task and all its subtasks.

    Parameters
    ----------
    task_id:
        Numeric Teamwork task ID to delete.
    **kwargs:
        Extra arguments forwarded to :pyfunc:`requests.delete`.

    Returns
    -------
    requests.Response
        Typically empty body with 204 No Content status on success.
    """
    return _delete(f"/tasks/{task_id}.json", **kwargs)


# --------------------------------------------------------------------------- #
# Project categories
# --------------------------------------------------------------------------- #
def list_project_categories(query: Optional[Dict[str, Any]] = None, **query_params):
    """
    GET /projectcategories.json – List project categories visible to the
    authenticated user.

    Any query-string filter supported by the Teamwork endpoint may be supplied,
    including:

    • searchTerm (str) – filter by category name  
    • onlyStarredProjects (bool) – include only starred projects in counts  
    • projectStatuses (list[str]) – restrict to specific project statuses  
    • ids (list[int]) – restrict to specific category IDs  
    • fields[projectcategories] (list[str]) – restrict returned fields
      (``id``, ``name``, ``color``, ``count``, ``parent``, ``parentId``)

    Parameters
    ----------
    query:
        Optional explicit dict of query parameters.
    **query_params:
        Additional query parameters passed as keyword arguments.

    Returns
    -------
    requests.Response
        The JSON body looks like ``{"projectcategories": [...], ...}``.
    """
    params = {**(query or {}), **query_params}
    return _get("/projectcategories.json", params=_serialize_params(params))
