"""Sentiment Analyst Agent."""

from __future__ import annotations

import os
from typing import Any

from tools.bus import ToolBus


class SentimentAnalystAgent:
    async def run(self, state: dict[str, Any], bus: ToolBus) -> dict[str, Any]:
        result = await bus.call(
            "news_search",
            {
                "query": state["query"],
                "max_results": state.get("news_max_results", 3),
            },
            role="sentiment",
            timeout_seconds=state.get("news_timeout_seconds"),
        )
        state.setdefault("tool_outputs", {})["news_search"] = result.data
        state.setdefault("tool_records", []).append(result.record)

        news_results = []
        if isinstance(result.data, dict):
            news_results = result.data.get("results") or []

            if result.data.get("error"):
                state.setdefault("warnings", []).append(
                    f"news_search failed: {result.data.get('error')}"
                )

        if not news_results and not os.getenv("TAVILY_API_KEY"):
            state.setdefault("warnings", []).append(
                "TAVILY_API_KEY 未配置，当前无法使用真实 Tavily 新闻检索。"
            )

        return state
