"""
HTTP fetching helpers (sync + async) using httpx.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from topscrape.exceptions import FetchError

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; topscrape/0.1; " "+https://github.com/ronaldgosso/topscrape)"
    )
}
DEFAULT_TIMEOUT = 15.0


def fetch_sync(
    url: str,
    headers: Mapping[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    **kwargs: Any,
) -> str:
    """
    Fetch *url* synchronously and return the response body as a string.

    Raises
    ------
    FetchError
        On any non-2xx response or network error.
    """
    merged_headers: dict[str, str] = {**DEFAULT_HEADERS, **(headers or {})}
    try:
        response = httpx.get(
            url,
            headers=merged_headers,
            timeout=timeout,
            follow_redirects=True,
            **kwargs,
        )
        response.raise_for_status()
        return response.text
    except httpx.HTTPStatusError as exc:
        raise FetchError(url, exc.response.status_code) from exc
    except httpx.RequestError as exc:
        raise FetchError(url, message=str(exc)) from exc


async def fetch_async(
    url: str,
    headers: Mapping[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    **kwargs: Any,
) -> str:
    """
    Async version of :func:`fetch_sync`.
    """
    merged_headers: dict[str, str] = {**DEFAULT_HEADERS, **(headers or {})}
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(
                url,
                headers=merged_headers,
                timeout=timeout,
                **kwargs,
            )
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as exc:
            raise FetchError(url, exc.response.status_code) from exc
        except httpx.RequestError as exc:
            raise FetchError(url, message=str(exc)) from exc
