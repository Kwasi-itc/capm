"""
aider.api
~~~~~~~~~

Lightweight wrapper around the ``requests`` package that offers a
simple, unified interface for the common HTTP verbs.  It can be used
two different ways:

1.  Instantiate ``ApiClient`` when you need an isolated client instance:

        from aider.api import ApiClient

        api = ApiClient(base_url="https://example.com/api")
        resp = api.get("/users", params={"active": True}).json()

2.  Or use the module-level helpers which share a single internal
    session:

        from aider import api

        data = api.get("https://httpbin.org/get").json()
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Union

import requests


class ApiError(Exception):
    """Raised when a request fails (non-2xx or transport error)."""


class ApiClient:
    """
    Simple convenience wrapper around :pyclass:`requests.Session`.

    Parameters
    ----------
    base_url:
        A prefix that is automatically prepended to every relative path you pass
        to :pyfunc:`request`.  Leave it empty to work with absolute URLs.
    timeout:
        Socket timeout (seconds) applied to every request unless you override it
        per call.
    headers:
        Default headers applied to every request (merged with per-call headers).
    """

    def __init__(
        self,
        base_url: str = "",
        timeout: Union[int, float] = 30,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        if headers:
            self.session.headers.update(headers or {})

    # --------------------------------------------------------------------- #
    # internal helpers
    # --------------------------------------------------------------------- #
    def _prepare_url(self, path: str) -> str:
        """Return an absolute URL from *path*."""
        if path.startswith(("http://", "https://")):
            return path
        if not self.base_url:
            # No base_url -> treat *path* as absolute already.
            return path.lstrip("/")
        return f"{self.base_url}/{path.lstrip('/')}"

    # --------------------------------------------------------------------- #
    # public API
    # --------------------------------------------------------------------- #
    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        """
        Generic request helper used by the verb-specific shortcuts.

        Raises
        ------
        ApiError
            When ``requests`` raises or the response status code is >=400.
        """
        url = self._prepare_url(path)
        try:
            resp = self.session.request(
                method=method.upper(),
                url=url,
                timeout=kwargs.pop("timeout", self.timeout),
                **kwargs,
            )
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            raise ApiError(str(exc)) from exc

    # Verb-specific shortcuts ------------------------------------------------
    def get(self, path: str, **kwargs) -> requests.Response:   # noqa: D401
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs) -> requests.Response:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.request("DELETE", path, **kwargs)

    # Lifecycle -------------------------------------------------------------
    def close(self) -> None:
        """Explicitly close the underlying :pyclass:`requests.Session`."""
        self.session.close()

    # Context-manager support ----------------------------------------------
    def __enter__(self) -> "ApiClient":
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: D401
        self.close()


# ---------------------------------------------------------------------------- #
# Module-level helpers that use a shared singleton session
# ---------------------------------------------------------------------------- #
_default_client: Optional[ApiClient] = None


def _client() -> ApiClient:
    global _default_client
    if _default_client is None:
        _default_client = ApiClient()
    return _default_client


def get(path: str, **kwargs) -> requests.Response:
    return _client().get(path, **kwargs)


def post(path: str, **kwargs) -> requests.Response:
    return _client().post(path, **kwargs)


def put(path: str, **kwargs) -> requests.Response:
    return _client().put(path, **kwargs)


def patch(path: str, **kwargs) -> requests.Response:
    return _client().patch(path, **kwargs)


def delete(path: str, **kwargs) -> requests.Response:
    return _client().delete(path, **kwargs)
