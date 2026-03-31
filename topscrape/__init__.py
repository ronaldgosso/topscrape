"""
topscrape — Declarative, resilient, and typed web scraping.
"""

from topscrape.exceptions import (
    FetchError,
    ParseError,
    ScrapeError,
    SelectorDriftWarning,
)
from topscrape.fields import Field
from topscrape.models import ScraperModel

__version__ = "0.1.4"
__all__ = [
    "ScraperModel",
    "Field",
    "ScrapeError",
    "FetchError",
    "ParseError",
    "SelectorDriftWarning",
]
