"""
topscrape — Declarative, resilient, and typed web scraping.
"""

from topscrape.models import ScraperModel
from topscrape.fields import Field
from topscrape.exceptions import (
    ScrapeError,
    FetchError,
    ParseError,
    SelectorDriftWarning,
)

__version__ = "0.1.0"
__all__ = [
    "ScraperModel",
    "Field",
    "ScrapeError",
    "FetchError",
    "ParseError",
    "SelectorDriftWarning",
]
