"""Tests for Phase 5 – CrawlerEngine static helpers."""

from __future__ import annotations

from unipaith.crawler.engine import CrawlerEngine


async def test_clean_html():
    html = "<html><head><script>bad</script></head><body><p>good stuff</p></body></html>"
    result = CrawlerEngine.clean_html(html)
    assert "good stuff" in result
    assert "bad" not in result


async def test_extract_links():
    html = """
    <html><body>
        <a href="/programs/cs">CS</a>
        <a href="https://example.edu/about">About</a>
        <a href="https://other-domain.com/page">External</a>
    </body></html>
    """
    links = CrawlerEngine._extract_links(html, "https://example.edu", None)

    assert "https://example.edu/programs/cs" in links
    assert "https://example.edu/about" in links
    # External link should be excluded
    assert "https://other-domain.com/page" not in links
