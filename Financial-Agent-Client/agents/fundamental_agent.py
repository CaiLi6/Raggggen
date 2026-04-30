"""Fundamental Analyst Agent."""

from __future__ import annotations

from typing import Any

from tools.bus import ToolBus


class FundamentalAnalystAgent:
    async def run(self, state: dict[str, Any], bus: ToolBus) -> dict[str, Any]:
        result = await bus.call(
            "rag_search",
            {
                "query": state["query"],
                "collection": state.get("collection"),
                "top_k": state.get("rag_top_k", 5),
            },
            role="fundamental",
            timeout_seconds=state.get("rag_timeout_seconds"),
        )
        state.setdefault("tool_outputs", {})["rag_search"] = result.data
        state.setdefault("tool_records", []).append(result.record)
        return state
