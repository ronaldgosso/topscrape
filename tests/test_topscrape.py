"""
Tests for topscrape.
"""
from __future__ import annotations

import pytest
import warnings

import parsel

from topscrape import Field, ScraperModel
from topscrape.exceptions import ParseError, SelectorDriftWarning
from topscrape.selectors.engine import resolve_field


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

SAMPLE_HTML = """
<html>
<head><title>Test Page</title></head>
<body>
  <h1 class="title">Best Laptop 2024</h1>
  <span class="product-price">$1,299.99</span>
  <a href="/buy/123" class="buy-link">Buy Now</a>
  <ul class="features">
    <li>16GB RAM</li>
    <li>1TB SSD</li>
    <li>4K Display</li>
  </ul>
  <div data-rating="4.7">Rating</div>
</body>
</html>
"""


@pytest.fixture
def sel() -> parsel.Selector:
    return parsel.Selector(text=SAMPLE_HTML)


# ─────────────────────────────────────────────
# resolve_field tests
# ─────────────────────────────────────────────

class TestResolveField:
    def test_css_primary_match(self, sel):
        value, idx = resolve_field(sel, ["h1.title"], None, False)
        assert value == "Best Laptop 2024"
        assert idx == 0

    def test_css_fallback_used(self, sel):
        value, idx = resolve_field(sel, [".nonexistent", "h1.title"], None, False)
        assert value == "Best Laptop 2024"
        assert idx == 1

    def test_xpath_match(self, sel):
        value, idx = resolve_field(sel, ["//title"], None, False)
        assert value == "Test Page"
        assert idx == 0

    def test_attr_extraction(self, sel):
        value, idx = resolve_field(sel, ["a.buy-link"], "href", False)
        assert value == "/buy/123"
        assert idx == 0

    def test_data_attr_extraction(self, sel):
        value, idx = resolve_field(sel, ["[data-rating]"], "data-rating", False)
        assert value == "4.7"
        assert idx == 0

    def test_multiple_values(self, sel):
        value, idx = resolve_field(sel, [".features li"], None, True)
        assert isinstance(value, list)
        assert len(value) == 3
        assert "16GB RAM" in value

    def test_no_match_returns_none(self, sel):
        value, idx = resolve_field(sel, [".does-not-exist", "#also-missing"], None, False)
        assert value is None
        assert idx == -1

    def test_regex_selector(self, sel):
        value, idx = resolve_field(sel, [r"r:\$[\d,]+\.\d{2}"], None, False)
        assert value == "$1,299.99"
        assert idx == 0

    def test_all_selectors_exhausted(self, sel):
        value, idx = resolve_field(sel, [".a", ".b", ".c"], None, False)
        assert value is None
        assert idx == -1


# ─────────────────────────────────────────────
# ScraperModel tests
# ─────────────────────────────────────────────

class TestScraperModel:

    def test_basic_parsing(self):
        class Product(ScraperModel):
            title: str = Field(selectors=["h1.title"])
            price: str = Field(selectors=[".product-price"])

        p = Product.from_html(SAMPLE_HTML)
        assert p.title == "Best Laptop 2024"
        assert p.price == "$1,299.99"

    def test_transform_applied(self):
        class Product(ScraperModel):
            price: float = Field(
                selectors=[".product-price"],
                transform=lambda v: v.replace("$", "").replace(",", ""),
            )

        p = Product.from_html(SAMPLE_HTML)
        assert p.price == pytest.approx(1299.99)

    def test_fallback_emits_drift_warning(self):
        class Product(ScraperModel):
            title: str = Field(selectors=[".missing-class", "h1.title"])

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            p = Product.from_html(SAMPLE_HTML)
            drift_warnings = [x for x in w if issubclass(x.category, SelectorDriftWarning)]
            assert len(drift_warnings) == 1
            assert "title" in str(drift_warnings[0].message)
            assert ".missing-class" in str(drift_warnings[0].message)

        assert p.title == "Best Laptop 2024"

    def test_required_field_raises_parse_error(self):
        class Product(ScraperModel):
            sku: str = Field(selectors=[".sku", "#product-id"])

        with pytest.raises(ParseError) as exc_info:
            Product.from_html(SAMPLE_HTML)

        assert "sku" in str(exc_info.value)

    def test_optional_field_uses_default(self):
        class Product(ScraperModel):
            title: str = Field(selectors=["h1.title"])
            badge: str = Field(selectors=[".badge"], default="N/A")

        p = Product.from_html(SAMPLE_HTML)
        assert p.badge == "N/A"

    def test_multiple_values(self):
        class Page(ScraperModel):
            features: list[str] = Field(selectors=[".features li"], multiple=True)

        p = Page.from_html(SAMPLE_HTML)
        assert len(p.features) == 3

    def test_attr_extraction_in_model(self):
        class Page(ScraperModel):
            buy_url: str = Field(selectors=["a.buy-link"], attr="href")

        p = Page.from_html(SAMPLE_HTML)
        assert p.buy_url == "/buy/123"

    def test_xpath_in_model(self):
        class Page(ScraperModel):
            page_title: str = Field(selectors=["//title"])

        p = Page.from_html(SAMPLE_HTML)
        assert p.page_title == "Test Page"

    def test_from_selector(self):
        class Product(ScraperModel):
            title: str = Field(selectors=["h1.title"])

        sel = parsel.Selector(text=SAMPLE_HTML)
        p = Product.from_selector(sel)
        assert p.title == "Best Laptop 2024"

    def test_pydantic_type_coercion(self):
        class Product(ScraperModel):
            rating: float = Field(
                selectors=["[data-rating]"],
                attr="data-rating",
            )

        p = Product.from_html(SAMPLE_HTML)
        assert isinstance(p.rating, float)
        assert p.rating == pytest.approx(4.7)

    def test_inheritance(self):
        class BasePage(ScraperModel):
            title: str = Field(selectors=["h1.title"])

        class ProductPage(BasePage):
            price: str = Field(selectors=[".product-price"])

        p = ProductPage.from_html(SAMPLE_HTML)
        assert p.title == "Best Laptop 2024"
        assert p.price == "$1,299.99"


# ─────────────────────────────────────────────
# CLI tests
# ─────────────────────────────────────────────

class TestCLI:
    def test_cli_imports(self):
        from topscrape.cli import build_parser
        parser = build_parser()
        assert parser is not None
