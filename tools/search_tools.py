"""Search tools — free search via DuckDuckGo, MCP web search server, and optional paid APIs.

Search priority:
  1. MCP Web Search Server (your deployed Render server — DuckDuckGo + fetch_page)
  2. DuckDuckGo local fallback (ddgs library — no API key)
  3. Google / Brave (optional paid fallbacks if API keys configured)
"""

import json
import logging

import httpx
from langchain.tools import tool

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MCP Web Search Server (deployed on Render)
# ---------------------------------------------------------------------------

MCP_WEB_SEARCH_URL = "https://mcp-web-search-nwgd.onrender.com/mcp"


@tool
def web_search(query: str, num_results: int = 10) -> str:
    """Search the web using the MCP Web Search Server (DuckDuckGo backend).

    This is the primary free search tool — no API key required.
    Connects to your deployed MCP server on Render.

    Args:
        query: Search query to execute
        num_results: Number of results to return (1-20, default 10)

    Returns:
        Search results with titles, URLs, and snippets.
    """
    try:
        # Use the MCP server's legacy REST endpoint for simplicity
        response = httpx.post(
            f"{MCP_WEB_SEARCH_URL}/tools/web_search",
            json={"query": query, "num_results": num_results},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        # MCP server returns {"results": [...]} on success
        results = data.get("results", data) if isinstance(data, dict) else data

        if not results:
            return _fallback_duckduckgo(query, num_results)

        if isinstance(results, list):
            formatted = []
            for i, item in enumerate(results, 1):
                title = item.get("title", "No title")
                url = item.get("url", item.get("href", ""))
                snippet = item.get("snippet", item.get("body", "No description"))
                formatted.append(f"[{i}] {title}\n    URL: {url}\n    {snippet}")
            return f"WEB SEARCH RESULTS for '{query}':\n\n" + "\n\n".join(formatted)

        # If results is a string or other format, return as-is
        return f"WEB SEARCH RESULTS for '{query}':\n\n{results}"

    except httpx.HTTPStatusError as e:
        logger.warning("MCP web search HTTP error %s, falling back to local DDG", e.response.status_code)
        return _fallback_duckduckgo(query, num_results)
    except Exception as e:
        logger.warning("MCP web search failed (%s), falling back to local DDG", e)
        return _fallback_duckduckgo(query, num_results)


@tool
def fetch_web_page(url: str) -> str:
    """Fetch and extract text content from a web page using the MCP Web Search Server.

    Uses the MCP server's fetch_page tool which fetches HTML and extracts
    readable text via BeautifulSoup.

    Args:
        url: The URL to fetch and extract content from

    Returns:
        Extracted text content from the page.
    """
    try:
        response = httpx.post(
            f"{MCP_WEB_SEARCH_URL}/tools/fetch_page",
            json={"url": url},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        content = data.get("content", data.get("text", data)) if isinstance(data, dict) else data

        if isinstance(content, str) and content:
            return f"PAGE CONTENT from {url}:\n\n{content}"
        elif isinstance(content, dict):
            text = content.get("text", content.get("content", json.dumps(content, indent=2)))
            return f"PAGE CONTENT from {url}:\n\n{text}"

        return f"PAGE CONTENT from {url}:\n\n{json.dumps(data, indent=2) if isinstance(data, dict) else str(data)}"

    except httpx.HTTPStatusError as e:
        logger.error("MCP fetch_page HTTP error: %s", e.response.status_code)
        return f"Failed to fetch {url}: HTTP {e.response.status_code}"
    except Exception as e:
        logger.error("MCP fetch_page failed: %s", e)
        return f"Failed to fetch {url}: {e}"


# ---------------------------------------------------------------------------
# Local DuckDuckGo fallback (no API key, no MCP server needed)
# ---------------------------------------------------------------------------

def _fallback_duckduckgo(query: str, num_results: int = 10) -> str:
    """Local DuckDuckGo search fallback using the ddgs library."""
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))

        if not results:
            return f"No DuckDuckGo search results for: {query}"

        formatted = []
        for i, item in enumerate(results, 1):
            title = item.get("title", "No title")
            url = item.get("href", item.get("url", ""))
            snippet = item.get("body", item.get("snippet", "No description"))
            formatted.append(f"[{i}] {title}\n    URL: {url}\n    {snippet}")

        return f"DUCKDUCKGO SEARCH RESULTS for '{query}':\n\n" + "\n\n".join(formatted)

    except Exception as e:
        logger.error("DuckDuckGo fallback failed: %s", e)
        return f"DuckDuckGo search error: {e}"


@tool
def duckduckgo_search(query: str, max_results: int = 10) -> str:
    """Search the web using DuckDuckGo directly (local, no API key).

    This is a local fallback that does not require any server or API key.
    Uses the ddgs (DuckDuckGo Search) library.

    Args:
        query: Search query to execute
        max_results: Maximum number of results to return (default: 10)

    Returns:
        Search results with titles, URLs, and snippets.
    """
    return _fallback_duckduckgo(query, max_results)


# ---------------------------------------------------------------------------
# Optional paid API fallbacks (only active if API keys are configured)
# ---------------------------------------------------------------------------

GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


@tool
def google_search(query: str, max_results: int = 5) -> str:
    """Search the web using Google Custom Search API (requires API key).

    Only available if GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX are configured.
    Falls back to DuckDuckGo if not configured.

    Args:
        query: Search query to execute
        max_results: Maximum number of results to return (default: 5)

    Returns:
        Search results with titles, snippets, and URLs.
    """
    if not settings.google_search_api_key:
        return _fallback_duckduckgo(query, max_results)

    try:
        params = {
            "key": settings.google_search_api_key,
            "cx": settings.google_search_cx,
            "q": query,
            "num": max_results,
        }

        response = httpx.get(GOOGLE_SEARCH_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        results = data.get("items", [])
        if not results:
            return _fallback_duckduckgo(query, max_results)

        formatted = []
        for i, item in enumerate(results, 1):
            title = item.get("title", "No title")
            link = item.get("link", "")
            snippet = item.get("snippet", "No snippet")
            formatted.append(f"[{i}] {title}\n    URL: {link}\n    {snippet}")

        return f"GOOGLE SEARCH RESULTS for '{query}':\n\n" + "\n\n".join(formatted)

    except httpx.HTTPStatusError as e:
        logger.error("Google search HTTP error: %s", e)
        return _fallback_duckduckgo(query, max_results)
    except Exception as e:
        logger.error("Google search failed: %s", e)
        return _fallback_duckduckgo(query, max_results)


@tool
def brave_search(query: str, max_results: int = 5) -> str:
    """Search the web using Brave Search API (requires API key).

    Only available if BRAVE_SEARCH_API_KEY is configured.
    Falls back to DuckDuckGo if not configured.

    Args:
        query: Search query to execute
        max_results: Maximum number of results to return (default: 5)

    Returns:
        Search results with titles, snippets, and URLs.
    """
    if not settings.brave_search_api_key:
        return _fallback_duckduckgo(query, max_results)

    try:
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": settings.brave_search_api_key,
        }
        params = {
            "q": query,
            "count": max_results,
        }

        response = httpx.get(
            BRAVE_SEARCH_URL, headers=headers, params=params, timeout=15
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("web", {}).get("results", [])
        if not results:
            return _fallback_duckduckgo(query, max_results)

        formatted = []
        for i, item in enumerate(results, 1):
            title = item.get("title", "No title")
            url = item.get("url", "")
            description = item.get("description", "No description")
            formatted.append(f"[{i}] {title}\n    URL: {url}\n    {description}")

        return f"BRAVE SEARCH RESULTS for '{query}':\n\n" + "\n\n".join(formatted)

    except httpx.HTTPStatusError as e:
        logger.error("Brave search HTTP error: %s", e)
        return _fallback_duckduckgo(query, max_results)
    except Exception as e:
        logger.error("Brave search failed: %s", e)
        return _fallback_duckduckgo(query, max_results)


# ---------------------------------------------------------------------------
# Tool exports — used by agents
# ---------------------------------------------------------------------------

# Primary search tools (free, no API key)
PRIMARY_SEARCH_TOOLS = [web_search, duckduckgo_search, fetch_web_page]

# All search tools (includes optional paid APIs)
ALL_SEARCH_TOOLS = [web_search, duckduckgo_search, fetch_web_page, google_search, brave_search]
