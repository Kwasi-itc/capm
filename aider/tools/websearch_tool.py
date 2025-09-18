"""
WebSearch tool

Provides up-to-date web search results that the LLM can cite when its training
data might be stale.  Utilises the public DuckDuckGo search API (via the
``duckduckgo_search`` package) so no additional API keys are required.

Returned content is plain text, formatted as numbered result blocks.

Limitations
-----------
* DDG currently geo-locks some results; the search API is therefore configured
  for the `us-en` region in line with the tool spec.
* Only the top ``MAX_RESULTS`` hits are returned.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List
from urllib.parse import urlparse

from duckduckgo_search import ddgs  # type: ignore

from aider.tools.base_tool import BaseTool, ToolError


class WebSearchTool(BaseTool):
    # -------------------- metadata visible to the LLM -----------------
    name = "WebSearch"
    description = (
        "- Allows the assistant to search the web and use the results to inform responses\n"
        "- Provides up-to-date information for current events and recent data\n"
        "- Returns search result information formatted as search result blocks\n"
        "- Use this tool for accessing information beyond the model's knowledge cutoff\n"
        "- Searches are performed automatically within a single API call\n\n"
        "Usage notes:\n"
        "  - Domain filtering is supported to include or block specific websites\n"
        "  - Web search is only available in the US (results use `us-en` region)\n"
        "  - Account for *Today's date* in <env> when crafting queries\n"
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "minLength": 2,
                "description": "The search query to use",
            },
            "allowed_domains": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Only include search results from these domains",
            },
            "blocked_domains": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Never include search results from these domains",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    }

    # -------------------------- implementation ------------------------
    _TTL = 10 * 60  # seconds
    _cache: dict[str, tuple[float, List[Dict[str, str]]]] = {}
    MAX_RESULTS = 8

    # Helper -----------------------------------------------------------
    @staticmethod
    def _domain(url: str) -> str:
        return urlparse(url).netloc.lower()

    def _filter_results(
        self,
        results: List[Dict[str, str]],
        allowed: List[str] | None,
        blocked: List[str] | None,
    ) -> List[Dict[str, str]]:
        allowed = [d.lower() for d in allowed or []]
        blocked = [d.lower() for d in blocked or []]

        filtered: List[Dict[str, str]] = []
        for res in results:
            dom = self._domain(res["href"])
            if allowed and not any(dom.endswith(a) for a in allowed):
                continue
            if blocked and any(dom.endswith(b) for b in blocked):
                continue
            filtered.append(res)
        return filtered

    def _search(
        self, query: str, allowed: List[str] | None, blocked: List[str] | None
    ) -> List[Dict[str, str]]:
        now = time.time()
        cache_key = f"{query}|{','.join(sorted(allowed or []))}|{','.join(sorted(blocked or []))}"
        if cache_key in self._cache and now - self._cache[cache_key][0] < self._TTL:
            return self._cache[cache_key][1]

        try:
            # Use the newer ``ddgs`` context manager recommended by the library
            with ddgs() as search:
                raw_results = list(
                    search.text(
                        query,
                        region="us-en",
                        safesearch="moderate",
                        timelimit="y",  # last year
                        max_results=self.MAX_RESULTS * 2,
                    )
                )
        except Exception as err:
            raise ToolError(f"Search failed: {err}") from err

        selected = self._filter_results(raw_results, allowed, blocked)[: self.MAX_RESULTS]
        self._cache[cache_key] = (now, selected)
        return selected

    # -----------------------------------------------------------------
    def run(
        self,
        *,
        query: str,
        allowed_domains: List[str] | None = None,
        blocked_domains: List[str] | None = None,
    ) -> str:  # noqa: D401
        """
        Perform a web search and return formatted results.
        """
        results = self._search(query, allowed_domains, blocked_domains)

        if not results:
            return "No results."

        lines: List[str] = []
        for i, res in enumerate(results, 1):
            title = res.get("title") or "(no title)"
            url = res.get("href") or "(no url)"
            snippet = res.get("body") or ""
            lines.append(f"### Result {i}\nTitle: {title}\nURL: {url}\nSnippet: {snippet}\n")

        return "\n".join(lines)
