"""
HTTP fetching helpers (sync + async) using httpx.
"""
from __future__ import annotations

import httpx

from topscrape.exceptions import FetchError

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; topscrape/0.1; "
        "+https://github.com/ronaldgosso/topscrape)"
    )
}
DEFAULT_TIMEOUT = 15.0


def fetch_sync(url: str, **kwargs: object) -> str:
    """
    Fetch *url* synchronously and return the response body as a string.

    Extra keyword arguments are forwarded to ``httpx.get``.

    Raises
    ------
    FetchError
        On any non-2xx response or network error.
    """
    headers = {**DEFAULT_HEADERS, **kwargs.pop("headers", {})}  # type: ignore[arg-type]
    timeout = kwargs.pop("timeout", DEFAULT_TIMEOUT)  # type: ignore[arg-type]
    try:
        response = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True, **kwargs)  # type: ignore[arg-type]
        response.raise_for_status()
        return response.text
    except httpx.HTTPStatusError as exc:
        raise FetchError(url, exc.response.status_code) from exc
    except httpx.RequestError as exc:
        raise FetchError(url, message=str(exc)) from exc


async def fetch_async(url: str, **kwargs: object) -> str:
    """
    Async version of :func:`fetch_sync`.
    """
    headers = {**DEFAULT_HEADERS, **kwargs.pop("headers", {})}  # type: ignore[arg-type]
    timeout = kwargs.pop("timeout", DEFAULT_TIMEOUT)  # type: ignore[arg-type]
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers, timeout=timeout, **kwargs)  # type: ignore[arg-type]
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as exc:
            raise FetchError(url, exc.response.status_code) from exc
        except httpx.RequestError as exc:
            raise FetchError(url, message=str(exc)) from exc
