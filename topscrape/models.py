"""
ScraperModel — the declarative base class for all scrapers.
"""
from __future__ import annotations

import logging
import warnings
from typing import Any

import parsel
from pydantic import BaseModel, model_validator

from topscrape.exceptions import ParseError, SelectorDriftWarning
from topscrape.fetcher import fetch_async, fetch_sync
from topscrape.fields import Field
from topscrape.selectors import resolve_field

logger = logging.getLogger("topscrape")


def _collect_scraper_fields(cls: type) -> dict[str, Field]:
    """
    Walk model_fields (Pydantic V2 stores our Field objects as the
    'default' of each FieldInfo) and collect every ScraperField.
    Inherits correctly because model_fields already merges the MRO.
    """
    fields: dict[str, Field] = {}
    for name, fi in cls.model_fields.items():  # type: ignore[attr-defined]
        if isinstance(fi.default, Field):
            fields[name] = fi.default
    return fields


class ScraperModel(BaseModel):
    """
    Declarative base for typed web scraping.

    Subclass this and annotate fields using :class:`~topscrape.Field`
    as the default value::

        class Product(ScraperModel):
            title: str = Field(selectors=["h1.title", "h1"])
            price: float = Field(
                selectors=[".price", "[data-price]"],
                transform=lambda v: v.replace("$", "").replace(",", ""),
            )

    Then call :meth:`from_url` or :meth:`from_html` to get a validated
    instance.
    """

    model_config = {"arbitrary_types_allowed": True}

    # ------------------------------------------------------------------ #
    # Pydantic hook — run extraction before __init__ validates types
    # ------------------------------------------------------------------ #

    @model_validator(mode="before")
    @classmethod
    def _run_extraction(cls, values: Any) -> Any:
        """
        When constructed with ``_html``/``_selector``, run the full
        extraction pipeline and replace the input dict with scraped data.
        """
        if not isinstance(values, dict):
            return values
        if "_html" not in values and "_selector" not in values:
            return values

        url = values.get("_url", "")
        if "_selector" in values:
            sel = values["_selector"]
        else:
            sel = parsel.Selector(text=values["_html"])

        return cls._extract(sel, source_url=url)

    # ------------------------------------------------------------------ #
    # Public constructors
    # ------------------------------------------------------------------ #

    @classmethod
    def from_html(cls, html: str, url: str = "") -> "ScraperModel":
        """Parse *html* and return a validated model instance."""
        return cls(**{"_html": html, "_url": url})

    @classmethod
    def from_url(cls, url: str, **fetch_kwargs: Any) -> "ScraperModel":
        """Fetch *url* synchronously and return a validated model instance."""
        html = fetch_sync(url, **fetch_kwargs)
        return cls.from_html(html, url=url)

    @classmethod
    async def from_url_async(cls, url: str, **fetch_kwargs: Any) -> "ScraperModel":
        """Async version of :meth:`from_url`."""
        html = await fetch_async(url, **fetch_kwargs)
        return cls.from_html(html, url=url)

    @classmethod
    def from_selector(cls, selector: parsel.Selector, url: str = "") -> "ScraperModel":
        """
        Build an instance directly from an existing ``parsel.Selector``.
        Useful when you want to reuse a fetched page for multiple models.
        """
        return cls(**{"_selector": selector, "_url": url})

    # ------------------------------------------------------------------ #
    # Internal extraction logic
    # ------------------------------------------------------------------ #

    @classmethod
    def _extract(cls, selector: parsel.Selector, source_url: str = "") -> dict[str, Any]:
        """
        Walk every Field annotation, run the selector chain, apply
        transforms, emit drift warnings, and return a dict ready for
        Pydantic validation.
        """
        scraper_fields = _collect_scraper_fields(cls)
        result: dict[str, Any] = {}

        for field_name, scrape_field in scraper_fields.items():
            raw_value, used_index = resolve_field(
                selector,
                scrape_field.selectors,
                scrape_field.attr,
                scrape_field.multiple,
            )

            # ---- Drift detection ----------------------------------------
            if used_index > 0:
                primary = scrape_field.selectors[0]
                fallback = scrape_field.selectors[used_index]
                msg = (
                    f"[Selector Drift] Field '{field_name}' on "
                    f"{'<' + source_url + '>' if source_url else 'parsed HTML'}: "
                    f"primary selector '{primary}' failed; "
                    f"used fallback[{used_index}] '{fallback}'."
                )
                logger.warning(msg)
                warnings.warn(msg, SelectorDriftWarning, stacklevel=6)

            # ---- Missing required field ----------------------------------
            if raw_value is None:
                if scrape_field.required:
                    raise ParseError(field_name, scrape_field.selectors)
                result[field_name] = scrape_field.default
                continue

            # ---- Optional transform -------------------------------------
            if scrape_field.transform is not None:
                if scrape_field.multiple and isinstance(raw_value, list):
                    raw_value = [scrape_field.transform(v) for v in raw_value]
                else:
                    raw_value = scrape_field.transform(raw_value)

            result[field_name] = raw_value

        return result
