"""
Exceptions and warnings for topscrape.
"""


class ScrapeError(Exception):
    """Base class for all topscrape errors."""


class FetchError(ScrapeError):
    """Raised when an HTTP request fails."""

    def __init__(self, url: str, status_code: int | None = None, message: str = ""):
        self.url = url
        self.status_code = status_code
        super().__init__(
            f"Failed to fetch '{url}'"
            + (f" (HTTP {status_code})" if status_code else "")
            + (f": {message}" if message else "")
        )


class ParseError(ScrapeError):
    """Raised when no selector matches a required field."""

    def __init__(self, field_name: str, selectors: list[str]):
        self.field_name = field_name
        self.selectors = selectors
        super().__init__(
            f"Field '{field_name}': all selectors exhausted with no match. "
            f"Tried: {selectors}"
        )


class SelectorDriftWarning(UserWarning):
    """
    Issued when a fallback selector was used instead of the primary one.
    This warns the developer that the site's HTML may have changed.
    """
