"""Tool Bus and default tool adapters."""

from __future__ import annotations

from typing import Any

from config.loader import ConfigLoader
from tools.bus import ToolBus
from tools.evaluator_tool import EvaluatorTool
from tools.market_data import MarketDataAdapter
from tools.news_search import NewsSearchAdapter
from tools.policy import ToolPolicy
from tools.rag_mcp import RAGMCPAdapter


def create_default_tool_bus(
    settings: dict[str, Any] | None = None,
    mock_tools: bool = False,
    policy: ToolPolicy | None = None,
) -> ToolBus:
    """Create a Tool Bus with the default research adapters registered."""

    loader = ConfigLoader()
    settings = settings or loader.load_settings()
    tool_settings = settings.get("tools", {})
    raw_policy = loader.load_tool_policy_raw()
    bus = ToolBus(policy=policy or ToolPolicy.from_raw(raw_policy))

    mock = mock_tools or bool(tool_settings.get("mock_external", False))
    bus.register(
        "rag_search",
        RAGMCPAdapter(mock=mock, top_k=int(tool_settings.get("rag_top_k", 5))),
    )
    bus.register(
        "news_search",
        NewsSearchAdapter(mock=mock, max_results=int(tool_settings.get("news_max_results", 3))),
    )
    bus.register("market_data", MarketDataAdapter())
    bus.register("evaluate_report", EvaluatorTool())
    return bus


__all__ = ["ToolBus", "ToolPolicy", "create_default_tool_bus"]
