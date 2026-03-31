<div align="center">
<h1>topscrape</h1>
<img width="1536" height="1024" alt="topscr" src="https://github.com/user-attachments/assets/926929bb-e04d-4556-9e08-144462961b22" />

[![PyPI version](https://img.shields.io/pypi/v/topscrape.svg)](https://pypi.org/project/topscrape/)
[![Python](https://img.shields.io/pypi/pyversions/topscrape.svg)](https://pypi.org/project/topscrape/)
[![CI](https://github.com/ronaldgosso/topscrape/actions/workflows/ci.yml/badge.svg)](https://github.com/ronaldgosso/topscrape/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/topscrape.svg)](https://pypi.org/project/topscrape/)


<br/>

**[📖 Landing Page](https://ronaldgosso.github.io/topscrape/)** &nbsp;·&nbsp;
**[📦 PyPI](https://pypi.org/project/topscrape/)** &nbsp;·&nbsp;
**[🐛 Issues](https://github.com/ronaldgosso/topscrape/issues)**

<br/>

</div>

> **Declarative, resilient, and typed web scraping.**  
> Define *what* you want — topscrape figures out *how* to get it, even when the site changes.
---

## ✨ Why topscrape?

Scrapers break when websites update their HTML. Fixing them means hunting down changed CSS selectors — tedious, repetitive, and always at the worst time.

### ❌ Standard approach — brittle

```python
soup = BeautifulSoup(html, "html.parser")
price = soup.select_one(".price")
if not price:
    price = soup.select_one(".cost")
````

Manual fallback. Manual debugging. Constant maintenance.

---

## ✅ The topscrape Approach

```python
from topscrape import ScraperModel, Field

class Product(ScraperModel):
    title: str = Field(selectors=["h1.title", "h1"])
    price: float = Field(
        selectors=[".product-price", "[data-price]", "//span[@itemprop='price']"],
        transform=lambda v: v.replace("$", "").replace(",", ""),
    )
    image: str = Field(selectors=["img.hero"], attr="src", default="")

product = Product.from_url("https://example.com/item/1")
print(product.price)
```

If `.product-price` disappears but `[data-price]` still works:

1. topscrape returns the correct value
2. Emits a **Selector Drift Warning**
3. Keeps your scraper alive

That’s resilience by design.

---

# 🚀 Features

| Feature             | Description                                 |
| ------------------- | ------------------------------------------- |
| Declarative models  | Define fields with `Field(selectors=[...])` |
| Selector chains     | CSS → XPath → Regex fallback                |
| Drift detection     | Warns before total breakage                 |
| Pydantic validation | Strong typing enforced                      |
| Transforms          | Clean data before validation                |
| Async ready         | `from_url_async()` supported                |
| CLI included        | Quick one-off extraction                    |

---

# 📦 Installation

```bash
pip install topscrape
```

Requires Python 3.9+.

---

# ⚡ Quick Start

## Google Colab Example - [Link](https://colab.research.google.com/drive/11xokydwd4tM0aKL9ofUYbtuPkclnnvLm?usp=sharing)

## Basic Extraction

```python
from topscrape import ScraperModel, Field

class Article(ScraperModel):
    title: str = Field(selectors=["h1", ".article-title"])
    author: str = Field(selectors=[".byline", "[rel='author']"], default="Unknown")
    content: str = Field(selectors=["article p", ".body-text"])

article = Article.from_html(html_string)
print(article.title)
```

---

## Fetch From URL

```python
product = Product.from_url("https://example.com/item/1")
print(product.title)
```

---

## Async Usage

```python
import asyncio

async def main():
    product = await Product.from_url_async("https://example.com/item/1")
    print(product.price)

asyncio.run(main())
```

---

## Multiple Values

```python
class Page(ScraperModel):
    tags: list[str] = Field(selectors=[".tag"], multiple=True)
    links: list[str] = Field(selectors=["nav a"], multiple=True, attr="href")
```

---

# 🛡 Drift Detection

If a fallback selector fires:

```
UserWarning: [Selector Drift] Field 'price':
primary selector '.product-price' failed;
used fallback '[data-price]'.
```

Catch programmatically:

```python
import warnings
from topscrape import SelectorDriftWarning

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    product = Product.from_url(url)

drifted = [x for x in w if issubclass(x.category, SelectorDriftWarning)]
```

---

# 🖥 CLI Usage

```bash
topscrape https://example.com "title"
topscrape https://example.com ".price" "[data-price]"
topscrape https://example.com "a.buy-link" --attr href
topscrape https://example.com "li.feature" --all
topscrape https://example.com "h1" --json
```

---

# 🧩 API Reference

## `Field`

| Parameter | Description                      |
| --------- | -------------------------------- |
| selectors | Ordered CSS / XPath / Regex list |
| attr      | Attribute to extract             |
| transform | Pre-validation function          |
| default   | Fallback value                   |
| multiple  | Return all matches               |

## `ScraperModel`

| Method         | Description             |
| -------------- | ----------------------- |
| from_html      | Parse raw HTML          |
| from_url       | Fetch & parse (sync)    |
| from_url_async | Fetch & parse (async)   |
| from_selector  | Parse existing selector |

---

# 👨‍💻 Developer Guide — Run & Contribute via GitHub

Want to run topscrape locally or contribute improvements? Follow this streamlined workflow.

---

## 🍴 1. Fork the Repository

1. Go to:
   [https://github.com/ronaldgosso/topscrape](https://github.com/ronaldgosso/topscrape)
2. Click **Fork**
3. Clone your fork

---

## 📥 2. Clone Your Fork

```bash
git clone https://github.com/<your-username>/topscrape.git
cd topscrape
```

Add upstream:

```bash
git remote add upstream https://github.com/ronaldgosso/topscrape.git
```

Sync later with:

```bash
git fetch upstream
git merge upstream/main
```

---

## 🐍 3. Create Virtual Environment

```bash
python -m venv .venv
```

Activate:

**Mac/Linux**

```bash
source .venv/bin/activate
```

**Windows**

```bash
.venv\Scripts\activate
```

---

## 📦 4. Install in Editable Mode

```bash
pip install -e ".[dev]"
```

Editable mode ensures changes apply instantly.

---

## 🧪 5. Run Tests

```bash
pytest
```

No green tests, no merge.

---

## 🧹 6. Lint & Type Check

```bash
ruff check .
black .
mypy topscrape/
```

Clean, typed, consistent.

---

## 🌿 7. Create Feature Branch

```bash
git checkout -b feature/your-feature
```

Never commit directly to `main`.

---

## 💾 8. Commit Properly

```bash
git commit -m "feat: improve fallback logging"
```

Conventional commit prefixes:

* feat:
* fix:
* docs:
* refactor:
* test:

---

## 🚀 9. Push & Open Pull Request

```bash
git push origin feature/your-feature
```

Then open a Pull Request against `ronaldgosso/main`.

---

# 🧠 Development Principles

topscrape prioritizes:

* Resilience over cleverness
* Declarative design
* Type safety
* Drift transparency

Every contribution should reduce brittleness.


---

# 🏆 Contribution Standards

Pull requests must:

* Pass CI
* Include tests (if applicable)
* Maintain backward compatibility
* Follow existing style

Quality > Speed.

---

# 📄 License

MIT © Ronald Isack Gosso
