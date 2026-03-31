"""
Low-level selector evaluation using parsel.
"""

from __future__ import annotations

import re
from typing import Any

import parsel


def _is_xpath(selector: str) -> bool:
    return selector.startswith("//") or selector.startswith("./")


def _is_regex(selector: str) -> bool:
    return selector.startswith("r:")


def _apply_selector(
    sel: parsel.Selector,
    selector_str: str,
    attr: str | None,
    multiple: bool,
) -> Any:
    """
    Apply a single selector string to a parsel.Selector and return the
    extracted value(s), or ``None`` if nothing matched.
    """
    if _is_regex(selector_str):
        pattern = selector_str[2:]
        html = sel.get() or ""
        matches = re.findall(pattern, html)
        if not matches:
            return None
        return matches if multiple else matches[0]

    if _is_xpath(selector_str):
        result = sel.xpath(selector_str)
    else:
        result = sel.css(selector_str)

    if not result:
        return None

    if attr:
        values = result.xpath(f"@{attr}").getall()
    else:
        values = result.xpath("normalize-space()").getall()
        if not any(v.strip() for v in values):
            # fall back to raw text
            values = result.css("::text").getall()
            values = [v.strip() for v in values if v.strip()]

    if not values:
        return None

    return values if multiple else values[0]


def resolve_field(
    sel: parsel.Selector,
    selectors: list[str],
    attr: str | None,
    multiple: bool,
) -> tuple[Any, int]:
    """
    Try each selector in order.  Return ``(value, index)`` where
    *index* is the position of the selector that matched (0 = primary).
    Return ``(None, -1)`` if nothing matched.
    """
    for idx, selector_str in enumerate(selectors):
        value = _apply_selector(sel, selector_str, attr, multiple)
        if value is not None and value != [] and value != "":
            return value, idx
    return None, -1
