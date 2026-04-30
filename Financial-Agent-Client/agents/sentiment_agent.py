"""Sentiment Analyst Agent."""

from __future__ import annotations

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
        return state
