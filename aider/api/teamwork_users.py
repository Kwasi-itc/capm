"""
Helpers for endpoints relating to the *current user* in the Teamwork.com API.

This mirrors the style of ``aider.api.teamwork_projects`` – each public
function is a thin wrapper that assembles the query-string parameters and then
delegates to the shared :pyfunc:`aider.api.teamwork.get` helper.

Only the subset of endpoints needed right now is implemented.  More can easily
be added following the same pattern.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .teamwork import get as _get
from .teamwork_projects import _serialize_params  # Re-use shared helper

__all__ = ["get_current_user"]


def get_current_user(
    *,
    query: Optional[Dict[str, Any]] = None,
    **query_params,
):
    """
    GET /me.json – details of the currently authenticated user.

    All keyword arguments (either in *query* or *query_params*) are passed
    straight through to Teamwork as query-string flags.  Boolean values are
    automatically converted to the ``"true"``/``"false"`` strings expected by
    the API.

    Examples
    --------
    >>> from aider.api.teamwork_users import get_current_user
    >>> user = get_current_user(fullProfile=True).json()["person"]
    """
    params: Dict[str, Any] = {}

    # Allow callers to supply a dict *or* bare keyword args – pattern copied
    # from aider.api.teamwork_projects.*
    if query:
        params.update(query)
    params.update(query_params)

    # Convert Python booleans → "true"/"false" strings as required by Teamwork.
    params = _serialize_params(params)

    return _get("/me.json", params=params)
