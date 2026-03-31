"""
Field — declares how to extract a value from HTML.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Field:
    """
    Declares extraction strategies for a single scraped field.

    Parameters
    ----------
    selectors:
        An ordered list of CSS selectors, XPath expressions, or regex
        patterns to try in sequence.  A string starting with ``//`` or
        ``./`` is treated as XPath; a string starting with ``r:`` is
        treated as a regex applied to the raw HTML.
    attr:
        HTML attribute to extract instead of the element's text content
        (e.g. ``"href"``, ``"src"``).  ``None`` means use ``.text``.
    transform:
        Optional callable applied to the raw extracted string *before*
        Pydantic validation.  Use this for cleaning, e.g.
        ``lambda v: v.replace("$", "")``.
    default:
        Value returned when every selector fails and the field is
        optional.  Pass ``...`` (Ellipsis) to mark the field as required
        (the default).
    multiple:
        If ``True``, return a list of all matching values instead of
        only the first one.
    """

    selectors: list[str]
    attr: str | None = None
    transform: Callable[[str], Any] | None = None
    default: Any = ...
    multiple: bool = False

    # Internal metadata — populated during extraction
    _used_selector_index: int = field(default=0, init=False, repr=False, compare=False)

    @property
    def required(self) -> bool:
        return self.default is ...
