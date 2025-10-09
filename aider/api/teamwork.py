"""
aider.api.teamwork
~~~~~~~~~~~~~~~~~~

Helpers for interacting with the Teamwork.com REST API.

The client automatically picks up an API token from either the explicit
``api_key`` argument *or* the ``TEAMWORK_API`` environment variable.
Likewise, the Teamwork sub-domain can be passed in via *domain* or
detected from ``TEAMWORK_DOMAIN``.  A minimal usage example::

    from aider.api.teamwork import get               # or TeamworkClient()
    users = get("/people.json").json()["people"]
"""
from __future__ import annotations

import os
from typing import Optional

from . import ApiClient, ApiError

__all__ = ["TeamworkClient", "get", "post", "put", "patch", "delete"]


class TeamworkClient(ApiClient):
    """
    Thin :pyclass:`aider.api.ApiClient` wrapper that pre-configures the base
    URL and Authorization header for Teamwork.

    Parameters
    ----------
    api_key:
        Personal access token.  Falls back to the ``TEAMWORK_API`` environment
        variable if omitted.
    domain:
        Teamwork sub-domain, eg ``mycompany`` for ``https://mycompany.teamwork.com``.
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

        domain = domain or os.getenv("TEAMWORK_DOMAIN")
        if not domain:
            raise ValueError(
                "Teamwork domain not provided and TEAMWORK_DOMAIN environment variable is not set"
            )

        base_url = f"https://{domain}.teamwork.com"
        # Teamwork accepts the token as basic auth user with no password *or*
        # as a Bearer header.  Bearer keeps things simple here.
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {api_key}"

        super().__init__(base_url=base_url, headers=headers, **kwargs)


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
