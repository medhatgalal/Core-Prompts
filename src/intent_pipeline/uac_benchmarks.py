from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    provider: str
    label: str
    url: str
    note: str

    def as_payload(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "label": self.label,
            "url": self.url,
            "note": self.note,
        }


def should_search_benchmarks(*, slug: str, fit_assessment: str, collection_type: str | None = None) -> bool:
    if fit_assessment in {"requires_adjustment", "manual_review"}:
        return True
    if collection_type in {"skill_family", "agent_family", "mixed_review"}:
        return True
    generic = {"architecture", "testing", "code-review", "docs", "review", "prompt", "prompts"}
    slug_bits = set(slug.replace("_", "-").split("-"))
    return bool(slug_bits & generic)


def benchmark_search(query: str, *, max_results: int = 4) -> list[dict[str, str]]:
    seen: set[str] = set()
    results: list[BenchmarkResult] = []
    for item in _github_repo_search(query, max_results=max_results):
        if item.url not in seen:
            seen.add(item.url)
            results.append(item)
    for item in _google_or_fallback_search(query, max_results=max_results):
        if item.url not in seen:
            seen.add(item.url)
            results.append(item)
    for item in _x_fallback_search(query, max_results=2):
        if item.url not in seen:
            seen.add(item.url)
            results.append(item)
    return [item.as_payload() for item in results[:max_results + 4]]


def _github_repo_search(query: str, *, max_results: int) -> Iterable[BenchmarkResult]:
    api = f"https://api.github.com/search/repositories?q={quote_plus(query)}&per_page={max_results}&sort=stars&order=desc"
    req = Request(api, headers={"User-Agent": "capability-fabric-uac", "Accept": "application/vnd.github+json"})
    try:
        with urlopen(req, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return []
    items = payload.get("items") or []
    out: list[BenchmarkResult] = []
    for item in items:
        full_name = str(item.get("full_name") or "")
        if not full_name:
            continue
        out.append(
            BenchmarkResult(
                provider="github",
                label=full_name,
                url=str(item.get("html_url") or ""),
                note=str(item.get("description") or "")[:160],
            )
        )
    return out


def _google_or_fallback_search(query: str, *, max_results: int) -> Iterable[BenchmarkResult]:
    api_key = os.environ.get("GOOGLE_API_KEY")
    cse_id = os.environ.get("GOOGLE_CSE_ID")
    if api_key and cse_id:
        api = (
            "https://www.googleapis.com/customsearch/v1?"
            f"key={quote_plus(api_key)}&cx={quote_plus(cse_id)}&q={quote_plus(query)}&num={max_results}"
        )
        req = Request(api, headers={"User-Agent": "capability-fabric-uac"})
        try:
            with urlopen(req, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            payload = {}
        items = payload.get("items") or []
        return [
            BenchmarkResult(
                provider="google",
                label=str(item.get("title") or "google-result"),
                url=str(item.get("link") or ""),
                note=str(item.get("snippet") or "")[:160],
            )
            for item in items
            if item.get("link")
        ]
    return _duckduckgo_html_search(query, provider="web", max_results=max_results)


def _x_fallback_search(query: str, *, max_results: int) -> Iterable[BenchmarkResult]:
    return _duckduckgo_html_search(f"site:x.com {query}", provider="x-search", max_results=max_results)


def _duckduckgo_html_search(query: str, *, provider: str, max_results: int) -> Iterable[BenchmarkResult]:
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    req = Request(url, headers={"User-Agent": "capability-fabric-uac"})
    try:
        with urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="replace")
    except Exception:
        return []
    results: list[BenchmarkResult] = []
    marker = 'result__a" href="'
    pos = 0
    while len(results) < max_results:
        start = html.find(marker, pos)
        if start == -1:
            break
        href_start = start + len(marker)
        href_end = html.find('"', href_start)
        title_end = html.find('</a>', href_end)
        if href_end == -1 or title_end == -1:
            break
        href = html[href_start:href_end]
        title = html[href_end + 2:title_end]
        snippet_marker = '<a class="result__snippet"'
        snippet = ''
        snippet_start = html.find(snippet_marker, title_end)
        if snippet_start != -1:
            snippet_text_start = html.find('>', snippet_start) + 1
            snippet_text_end = html.find('</a>', snippet_text_start)
            snippet = html[snippet_text_start:snippet_text_end]
        results.append(BenchmarkResult(provider=provider, label=_strip_html(title), url=href, note=_strip_html(snippet)[:160]))
        pos = title_end
    return results


def _strip_html(value: str) -> str:
    out = value.replace('&amp;', '&').replace('&quot;', '"').replace('&#x27;', "'")
    import re
    return re.sub(r'<[^>]+>', '', out).strip()
