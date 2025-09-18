"""
WebFetch tool

Fetches a web page, converts the HTML to markdown and (optionally) asks a
small/fast LLM to answer a user-supplied prompt about the fetched content.

A 15-minute in-memory cache avoids refetching the same URL repeatedly.
"""

from __future__ import annotations

import time
from typing import Tuple

import requests
import html2text
from urllib.parse import urlparse

from aider.tools.base_tool import BaseTool, ToolError


class WebFetchTool(BaseTool):
    # -------- metadata advertised to the LLM --------------------------
    name = "WebFetch"
    description = (
        "- Fetches content from a specified URL and processes it using an AI model\n"
        "- Takes a URL and a prompt as input\n"
        "- Fetches the URL content, converts HTML to markdown\n"
        "- Processes the content with the prompt using a small, fast model\n"
        "- Returns the model's response about the content\n"
        "- Use this tool when you need to retrieve and analyze web content\n\n"
        "Usage notes:\n"
        "  - IMPORTANT: If an MCP-provided web fetch tool is available, prefer using that tool "
        "instead of this one, as it may have fewer restrictions. All MCP-provided tools start "
        'with "mcp__".\n'
        "  - The URL must be a fully-formed valid URL\n"
        "  - HTTP URLs will be automatically upgraded to HTTPS\n"
        "  - The prompt should describe what information you want to extract from the page\n"
        "  - This tool is read-only and does not modify any files\n"
        "  - Results may be summarized if the content is very large\n"
        "  - Includes a self-cleaning 15-minute cache for faster responses when repeatedly "
        "accessing the same URL\n"
        "  - When a URL redirects to a different host, the tool will inform you and provide the "
        "redirect URL in a special format. You should then make a new WebFetch request with the "
        "redirect URL to fetch the content."
    )
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "format": "uri",
                "description": "The URL to fetch content from",
            },
            "prompt": {
                "type": "string",
                "description": "The prompt to run on the fetched content",
            },
        },
        "required": ["url", "prompt"],
        "additionalProperties": False,
    }

    # ------------------------ implementation --------------------------
    _TTL = 15 * 60  # 15 minutes
    _cache: dict[str, Tuple[float, str]] = {}

    @staticmethod
    def _upgrade_to_https(url: str) -> str:
        if url.startswith("http://"):
            return "https://" + url[len("http://") :]
        return url

    def _fetch_markdown(self, url: str) -> str:
        """
        Fetch the given URL, follow at most one redirect and convert the HTML
        response into markdown.  Results are cached for `_TTL` seconds.
        """
        url = self._upgrade_to_https(url)

        # Return cached copy if it is still fresh
        now = time.time()
        if url in self._cache and now - self._cache[url][0] < self._TTL:
            return self._cache[url][1]

        try:
            resp = requests.get(
                url,
                timeout=15,
                allow_redirects=False,
                headers={"User-Agent": "aider-webfetch/1.0"},
            )
        except Exception as err:
            raise ToolError(f"Network error while fetching {url}: {err}") from err

        # Handle (single-hop) redirects explicitly so the caller can decide
        if 300 <= resp.status_code < 400 and "Location" in resp.headers:
            redirect_url = resp.headers["Location"]
            # Absolute or relative?
            if redirect_url.startswith("/"):
                parsed = urlparse(url)
                redirect_url = f"{parsed.scheme}://{parsed.netloc}{redirect_url}"
            raise ToolError(f"redirect:{redirect_url}")

        if resp.status_code != 200:
            raise ToolError(f"HTTP {resp.status_code} when fetching {url}")

        # Convert HTML → markdown
        converter = html2text.HTML2Text()
        converter.ignore_images = True
        converter.ignore_links = False
        converter.body_width = 0
        markdown = converter.handle(resp.text)

        # Cache and return
        self._cache[url] = (now, markdown)
        return markdown

    # ----------------------------- API --------------------------------
    def run(self, *, url: str, prompt: str) -> str:  # noqa: D401
        """
        Fetch `url`, convert to markdown, then feed the markdown plus `prompt`
        into the weak (fast/cheap) LLM.  Return the LLM's answer.
        """
        markdown = self._fetch_markdown(url)

        # Guard against extremely long pages: truncate to ~6 000 tokens worth of content
        max_chars = 25_000
        if len(markdown) > max_chars:
            markdown = markdown[:max_chars] + "\n\n...[truncated]..."

        # If the coder is not attached (e.g. during unit tests) just return the markdown
        if not getattr(self, "coder", None):
            return markdown

        # Use the weak model to process the page quickly
        weak_model = self.coder.main_model.weak_model or self.coder.main_model
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": markdown},
        ]
        try:
            _hash, completion = weak_model.send_completion(
                messages, functions=None, stream=False, temperature=0
            )
            return completion.choices[0].message.content.strip()
        except Exception as err:
            # Fall back to returning raw markdown if the model call fails
            self.coder.io.tool_warning(f"WebFetch: LLM processing failed: {err}")
            return markdown
