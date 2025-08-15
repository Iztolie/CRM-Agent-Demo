import os
import json
import logging
import time
from typing import List, Dict, Any
from tavily import TavilyClient
from .config import config
from .utils import retry_with_backoff

logger = logging.getLogger(__name__)

class SearchProvider:
    """Abstract base class for search providers."""
    @retry_with_backoff()
    async def search(self, query: str) -> List[Dict[str, Any]]:  # pragma: no cover - interface
        raise NotImplementedError

class TavilySearchProvider(SearchProvider):
    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not set")
        placeholder_tokens = {"your_tavily_key_here", "your_tavily_api_key_here", "changeme", "placeholder"}
        if api_key.strip().lower() in placeholder_tokens or api_key.startswith("<"):
            raise ValueError("TAVILY_API_KEY appears to be a placeholder. Please set a real key in .env or environment.")
        self.client = TavilyClient(api_key=api_key)

    async def search(self, query: str) -> List[Dict[str, Any]]:
        start = time.time()
        results = self.client.search(query=query, max_results=config.max_search_results)
        elapsed = time.time() - start
        items = results.get("results", []) or []
        top_titles = [r.get("title") for r in items[:3]]
        logger.debug(
            "Tavily search query='%s' took=%.2fs count=%d top_titles=%s",
            query,
            elapsed,
            len(items),
            top_titles,
        )
        if not items:
            logger.warning("Tavily returned no results for query='%s'", query)
        if os.getenv("TAVILY_LOG_JSON"):
            # Truncate to avoid log flooding
            raw_snippet = json.dumps(results)[:2000]
            logger.debug("Tavily raw response (truncated): %s", raw_snippet)
        return items

PROVIDERS = {
    "tavily": TavilySearchProvider,
}

def get_search_provider() -> SearchProvider:
    cls = PROVIDERS.get(config.search_provider)
    if not cls:
        raise ValueError(f"Unknown search provider: {config.search_provider}")
    return cls()
