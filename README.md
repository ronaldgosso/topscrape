# topscrape

[![PyPI version](https://img.shields.io/pypi/v/topscrape.svg)](https://pypi.org/project/topscrape/)
[![Python](https://img.shields.io/pypi/pyversions/topscrape.svg)](https://pypi.org/project/topscrape/)
[![CI](https://github.com/ronaldgosso/topscrape/actions/workflows/ci.yml/badge.svg)](https://github.com/ronaldgosso/topscrape/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Declarative, resilient, and typed web scraping.**  
Define *what* you want — topscrape figures out *how* to get it, even when the site changes.

---

## The Problem

Scrapers break when websites update their HTML. Fixing them means hunting down changed CSS selectors — tedious, repetitive, and always at the worst time.

```python
# Standard approach — brittle
soup = BeautifulSoup(html, "html.parser")
price = soup.select_one(".price")       # breaks if class changes
if not price:
    price = soup.select_one(".cost")    # manual fallback, every time
```

## The Solution

```python
from topscrape import ScraperModel, Field

class Product(ScraperModel):
    title: str  = Field(selectors=["h1.title", "h1"])
    price: float = Field(
        selectors=[".product-price", "[data-price]", "//span[@itemprop='price']"],
        transform=lambda v: v.replace("$", "").replace(",", ""),
    )
    image: str  = Field(selectors=["img.hero"], attr="src", default="")

product = Product.from_url("https://example.com/item/1")
print(product.price)   # → 1299.99  (float, validated by Pydantic)
```

When `.product-price` disappears but `[data-price]` still works, topscrape:
1. Silently returns the correct value
2. Logs a **Selector Drift warning** — telling you *exactly* which field drifted and which fallback fired

---

## Features

| Feature | Description |
|---------|-------------|
| **Declarative models** | Define fields with `Field(selectors=[...])` — no imperative parsing |
| **Selector chains** | CSS → XPath → Regex tried in order; first match wins |
| **Drift detection** | Warns when a fallback fires, before your scraper fully breaks |
| **Pydantic validation** | Types are enforced — get `float`, not `"$19.99"` |
| **Transforms** | Clean raw strings before validation with a simple `lambda` |
| **Async ready** | `await Product.from_url_async(url)` with full `httpx` async support |
| **CLI included** | `topscrape <url> <selectors...>` for quick one-off extraction |

---

## Installation

```bash
pip install topscrape
```

Requires Python 3.9+.

---

## Quick Start

### 1 · Basic extraction

```python
from topscrape import ScraperModel, Field

class Article(ScraperModel):
    title:   str = Field(selectors=["h1", ".article-title"])
    author:  str = Field(selectors=[".byline", "[rel='author']"], default="Unknown")
    content: str = Field(selectors=["article p", ".body-text"])

article = Article.from_html(html_string)
print(article.title)
print(article.author)
```

### 2 · Fetch from a URL (sync)

```python
product = Product.from_url("https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html")
print(product.title)
```

### 3 · Async scraping

```python
import asyncio

async def main():
    product = await Product.from_url_async("https://example.com/item/1")
    print(product.price)

asyncio.run(main())
```

### 4 · Reuse a fetched page for multiple models

```python
import parsel, httpx

html = httpx.get("https://example.com").text
sel  = parsel.Selector(text=html)

product = Product.from_selector(sel)
metadata = PageMeta.from_selector(sel)
```

### 5 · Selector types

```python
class Demo(ScraperModel):
    # CSS selector (default)
    title:   str = Field(selectors=["h1.title"])

    # XPath — any string starting with // or ./
    author:  str = Field(selectors=["//span[@class='author']"])

    # Regex — prefix with r:
    version: str = Field(selectors=[r"r:v(\d+\.\d+\.\d+)"])

    # Fallback chain — CSS first, XPath second, regex third
    price:   str = Field(selectors=[".price", "//span[@itemprop='price']", r"r:\$[\d.]+"])
```

### 6 · Attribute extraction

```python
class Links(ScraperModel):
    hero_image: str = Field(selectors=["img.hero"],    attr="src")
    buy_url:    str = Field(selectors=["a.buy-button"], attr="href")
    rating:     str = Field(selectors=["div.stars"],    attr="data-score")
```

### 7 · Multiple values

```python
class Page(ScraperModel):
    tags:  list[str] = Field(selectors=[".tag"],     multiple=True)
    links: list[str] = Field(selectors=["nav a"],    multiple=True, attr="href")
```

---

## Drift Detection

When a fallback selector is used, topscrape emits a `SelectorDriftWarning`:

```
UserWarning: [Selector Drift] Field 'price' on <https://example.com/item/1>:
primary selector '.product-price' failed;
used fallback[1] '[data-price]'.
```

You can catch it programmatically:

```python
import warnings
from topscrape import SelectorDriftWarning

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    product = Product.from_url(url)

drifted = [x for x in w if issubclass(x.category, SelectorDriftWarning)]
if drifted:
    print("Site may have changed — update your selectors!")
```

---

## CLI

```bash
# Extract the page title
topscrape https://example.com "title"

# Try two selectors (fallback chain)
topscrape https://example.com ".price" "[data-price]"

# Extract an attribute
topscrape https://example.com "a.buy-link" --attr href

# Return all matches
topscrape https://example.com "li.feature" --all

# JSON output
topscrape https://example.com "h1" --json
```

---

## API Reference

### `Field`

| Parameter | Type | Description |
|-----------|------|-------------|
| `selectors` | `list[str]` | Ordered list of CSS, XPath (`//...`), or Regex (`r:...`) selectors |
| `attr` | `str \| None` | HTML attribute to extract (default: text content) |
| `transform` | `callable \| None` | Applied to raw string before Pydantic validation |
| `default` | `Any` | Value when all selectors fail. `...` = required (default) |
| `multiple` | `bool` | Return all matches as a list (default: `False`) |

### `ScraperModel`

| Method | Description |
|--------|-------------|
| `.from_html(html, url="")` | Parse raw HTML string |
| `.from_url(url, **kwargs)` | Fetch and parse synchronously |
| `await .from_url_async(url, **kwargs)` | Fetch and parse asynchronously |
| `.from_selector(selector, url="")` | Parse from existing `parsel.Selector` |

---

## Development

```bash
git clone https://github.com/ronaldgosso/topscrape
cd topscrape
pip install -e ".[dev]"

# Run tests
pytest

# Lint + format
ruff check .
black .

# Type check
mypy topscrape/
```

---

## License

MIT © [Ronald Isack Gosso](https://github.com/ronaldgosso)
