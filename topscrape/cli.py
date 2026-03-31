"""
topscrape CLI — quick scrape from the command line.

Usage
-----
    topscrape <url> <css_selector> [--attr ATTR] [--xpath] [--all]

Examples
--------
    topscrape https://example.com "h1"
    topscrape https://example.com ".price" --attr data-value
    topscrape https://example.com "//title" --xpath
    topscrape https://example.com "a" --attr href --all
"""

from __future__ import annotations

import argparse
import json
import sys

import parsel

from topscrape.exceptions import FetchError
from topscrape.fetcher import fetch_sync
from topscrape.selectors.engine import resolve_field


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="topscrape",
        description="Declarative, resilient web scraping — quick CLI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("url", help="Target URL to scrape")
    parser.add_argument(
        "selector",
        nargs="+",
        help="One or more selectors to try in order (fallback chain).",
    )
    parser.add_argument(
        "--attr",
        default=None,
        metavar="ATTR",
        help="Extract this HTML attribute instead of text content.",
    )
    parser.add_argument(
        "--all",
        dest="multiple",
        action="store_true",
        help="Return all matches instead of only the first.",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output result as JSON.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Request timeout in seconds (default: 15).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # ---- Fetch ----------------------------------------------------------
    try:
        html = fetch_sync(args.url, timeout=args.timeout)
    except FetchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # ---- Extract --------------------------------------------------------
    sel = parsel.Selector(text=html)
    value, used_index = resolve_field(
        sel,
        args.selector,
        args.attr,
        args.multiple,
    )

    if value is None:
        print(
            f"ERROR: No match found. Tried selectors: {args.selector}",
            file=sys.stderr,
        )
        return 2

    # ---- Drift notice ---------------------------------------------------
    if used_index > 0:
        print(
            f"[DRIFT WARNING] Primary selector '{args.selector[0]}' failed; "
            f"used fallback[{used_index}] '{args.selector[used_index]}'.",
            file=sys.stderr,
        )

    # ---- Output ---------------------------------------------------------
    if args.as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2))
    else:
        if isinstance(value, list):
            for item in value:
                print(item)
        else:
            print(value)

    return 0


if __name__ == "__main__":
    sys.exit(main())
