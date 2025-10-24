"""
aider.api.teamwork
~~~~~~~~~~~~~~~~~~

Helpers for interacting with the Teamwork.com REST API.

The client automatically picks up an API token from either the explicit
``api_key`` argument *or* the ``TEAMWORK_API`` environment variable.
Likewise, the Teamwork sub-domain can be passed in via *domain* or
detected from ``TEAMWORK_DOMAIN``.  A minimal usage example::

    from aider.api.teamwork import get               # or TeamworkClient()
    projects = get("/projects.json").json()["projects"]
"""
from __future__ import annotations

import os
from typing import Optional

from . import ApiClient, ApiError

__all__ = ["TeamworkClient", "get", "post", "put", "patch", "delete", "me"]


class TeamworkClient(ApiClient):
    """
    Thin :pyclass:`aider.api.ApiClient` wrapper that pre-configures the base
    URL and HTTP Basic authentication for Teamwork.

    Parameters
    ----------
    api_key:
        Personal access token.  Falls back to the ``TEAMWORK_API`` environment
        variable if omitted.
    domain:
        Teamwork sub-domain, eg ``itconsortium`` for ``https://itconsortium.teamwork.com``.
        Falls back to ``TEAMWORK_DOMAIN`` env var.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        **kwargs,
    ) -> None:
        api_key = api_key or os.getenv("TEAMWORK_API")
        if not api_key:
            raise ValueError(
                "Teamwork API token not provided and TEAMWORK_API environment variable is not set"
            )

        # Fall back to a project-wide default so callers don’t have to supply it
        # every time.  Override this by passing *domain* or setting
        # ``TEAMWORK_DOMAIN`` in the environment.
        domain = domain or os.getenv("TEAMWORK_DOMAIN") or "itconsortium"

        base_url = f"https://{domain}.teamwork.com/projects/api/v3"
        # Teamwork uses HTTP *Basic* auth where the API token is the **username**
        # and the password can be any dummy value.  We therefore rely on the
        # built-in requests ``auth`` mechanism instead of a Bearer header.
        headers = kwargs.pop("headers", {})
        super().__init__(base_url=base_url, headers=headers, **kwargs)

        # username = api_key, password = "x" (ignored by Teamwork)
        self.session.auth = (api_key, "x")

    # --------------------------------------------------------------------- #
    # Public helpers
    # --------------------------------------------------------------------- #
    def me(
        self,
        *,
        getPreferences: bool = False,
        fullProfile: bool = False,
        getDefaultFilters: bool = False,
        sharedFilter: bool = False,
        getAccounts: bool = False,
        includeAuth: bool = False,
        **kwargs,
    ):
        """
        Fetch details of the currently authenticated Teamwork user.

        Parameters correspond to the optional query-string flags documented by
        the Teamwork API.  Pass ``True`` to include a flag, leave ``False`` to
        omit it.

        Returns
        -------
        requests.Response
            Response object for GET /me.json
        """
        params = {
            "getPreferences": getPreferences,
            "fullProfile": fullProfile,
            "getDefaultFilters": getDefaultFilters,
            "sharedFilter": sharedFilter,
            "getAccounts": getAccounts,
            "includeAuth": includeAuth,
        }
        # Filter out params left at the default ``False`` value so the query
        # string stays short.
        params = {k: "true" for k, v in params.items() if v}
        return self.get("/me.json", params=params, **kwargs)


# --------------------------------------------------------------------------- #
# Module-level convenience helpers
# --------------------------------------------------------------------------- #
_default_tw_client: Optional[TeamworkClient] = None


def _tw() -> TeamworkClient:
    global _default_tw_client
    if _default_tw_client is None:
        _default_tw_client = TeamworkClient()
    return _default_tw_client


def get(path: str, **kwargs):
    return _tw().get(path, **kwargs)


def post(path: str, **kwargs):
    return _tw().post(path, **kwargs)


def put(path: str, **kwargs):
    return _tw().put(path, **kwargs)


def patch(path: str, **kwargs):
    return _tw().patch(path, **kwargs)


def delete(path: str, **kwargs):
    return _tw().delete(path, **kwargs)


def me(**kwargs):
    """
    Convenience wrapper around TeamworkClient.me().
    Mirrors the same keyword arguments.
    """
    return _tw().me(**kwargs)


