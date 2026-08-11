"""Dependency-free web research for generated standalone systems."""

import html
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    title: str
    url: str
    snippet: str


_USER_AGENT = "Mozilla/5.0 (AI Factory research agent)"


def _get(url: str, timeout: int = 15) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(2_000_000)
        return raw.decode("utf-8", errors="ignore")


def search(query: str, limit: int = 5) -> list[Source]:
    """Search the public web through DuckDuckGo's HTML endpoint."""
    query = " ".join(str(query).split())[:500]
    if not query:
        return []
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(query)
    page = _get(url)
    results: list[Source] = []
    pattern = re.compile(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
    for href, raw_title in pattern.findall(page):
        if len(results) >= limit:
            break
        clean = re.sub(r"<[^>]+>", " ", html.unescape(raw_title))
        clean = " ".join(clean.split())
        parsed = urllib.parse.urlparse(html.unescape(href))
        if parsed.scheme not in {"http", "https"}:
            continue
        results.append(Source(clean, html.unescape(href), ""))
    return results


def collect(query: str, limit: int = 5, max_chars: int = 5000) -> dict:
    """Return search results plus small source excerpts for evidence-aware agents."""
    sources = search(query, limit=limit)
    evidence = []
    for source in sources:
        try:
            page = _get(source.url)
            text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", page, flags=re.I | re.S)
            text = re.sub(r"<[^>]+>", " ", html.unescape(text))
            text = " ".join(text.split())
            evidence.append({"title": source.title, "url": source.url, "excerpt": text[:max_chars]})
        except Exception as exc:
            evidence.append({"title": source.title, "url": source.url, "excerpt": "", "error": str(exc)})
    return {"query": query, "sources": evidence}
