"""News and sentiment search adapter."""

from __future__ import annotations

import os
from typing import Any


class NewsSearchAdapter:
    def __init__(self, mock: bool = False, max_results: int = 3):
        self.mock = mock
        self.max_results = max_results

    async def __call__(self, query: str, max_results: int | None = None) -> dict[str, Any]:
        if self.mock:
            return {
                "provider": "mock_news",
                "results": [
                    {
                        "title": "Mock market sentiment digest",
                        "url": "mock://news/sentiment-digest",
                        "content": f"外部新闻模拟摘要：市场围绕“{query}”关注需求、利润率、政策和估值变化。",
                    }
                ],
            }

        if not os.getenv("TAVILY_API_KEY"):
            return {
                "provider": "tavily",
                "results": [],
                "error": "WEB_SEARCH_FAILED",
                "message": "TAVILY_API_KEY is not configured",
            }

        try:
            from infrastructure.tools import web_search_sentiment

            data = await web_search_sentiment(query)
        except Exception as exc:
            return {"provider": "tavily", "results": [], "error": "WEB_SEARCH_FAILED", "message": str(exc)}

        if data.get("error"):
            return {
                "provider": data.get("provider", "tavily"),
                "results": data.get("results") or [],
                "error": data.get("error", "WEB_SEARCH_FAILED"),
                "message": data.get("message", "news search failed"),
            }
        results = data.get("results") or []
        return {
            "provider": data.get("provider", "tavily"),
            "results": results[: max_results or self.max_results],
        }
