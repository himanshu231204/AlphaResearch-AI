"""Search tools — wraps Google Custom Search and Brave Search APIs."""

import logging

import httpx
from langchain.tools import tool

from app.config import settings

logger = logging.getLogger(__name__)

GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


@tool
def google_search(query: str, max_results: int = 5) -> str:
    """Search the web using Google Custom Search API.

    Args:
        query: Search query to execute
        max_results: Maximum number of results to return (default: 5)

    Returns:
        Search results with titles, snippets, and URLs.
    """
    if not settings.google_search_api_key:
        return "Google Search API key not configured. Set GOOGLE_SEARCH_API_KEY."

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
            return f"No Google search results for: {query}"

        formatted = []
        for i, item in enumerate(results, 1):
            title = item.get("title", "No title")
            link = item.get("link", "")
            snippet = item.get("snippet", "No snippet")
            formatted.append(f"[{i}] {title}\n    URL: {link}\n    {snippet}")

        return f"GOOGLE SEARCH RESULTS for '{query}':\n\n" + "\n\n".join(formatted)

    except httpx.HTTPStatusError as e:
        logger.error("Google search HTTP error: %s", e)
        return f"Google search error: {e.response.status_code}"
    except Exception as e:
        logger.error("Google search failed: %s", e)
        return f"Google search error: {e}"


@tool
def brave_search(query: str, max_results: int = 5) -> str:
    """Search the web using Brave Search API.

    Args:
        query: Search query to execute
        max_results: Maximum number of results to return (default: 5)

    Returns:
        Search results with titles, snippets, and URLs.
    """
    if not settings.brave_search_api_key:
        return "Brave Search API key not configured. Set BRAVE_SEARCH_API_KEY."

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
            return f"No Brave search results for: {query}"

        formatted = []
        for i, item in enumerate(results, 1):
            title = item.get("title", "No title")
            url = item.get("url", "")
            description = item.get("description", "No description")
            formatted.append(f"[{i}] {title}\n    URL: {url}\n    {description}")

        return f"BRAVE SEARCH RESULTS for '{query}':\n\n" + "\n\n".join(formatted)

    except httpx.HTTPStatusError as e:
        logger.error("Brave search HTTP error: %s", e)
        return f"Brave search error: {e.response.status_code}"
    except Exception as e:
        logger.error("Brave search failed: %s", e)
        return f"Brave search error: {e}"


ALL_SEARCH_TOOLS = [google_search, brave_search]
