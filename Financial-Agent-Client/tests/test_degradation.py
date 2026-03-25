from __future__ import annotations

from unittest.mock import patch

from langchain_core.messages import HumanMessage

from core.graph import workflow


def test_graph_degradation_reaches_agent_c_with_error_banner() -> None:
    app = workflow.compile()

    with patch("infrastructure.tools.mcp_query_knowledge_hub", side_effect=RuntimeError("mcp down")), \
        patch("infrastructure.tools.web_search_sentiment", side_effect=RuntimeError("web down")), \
        patch("agents.nodes.mcp_query_knowledge_hub", side_effect=RuntimeError("mcp down")), \
        patch("agents.nodes.web_search_sentiment", side_effect=RuntimeError("web down")):
        result = app.invoke(
            {"messages": [HumanMessage(content="请结合财报和舆情分析特斯拉")]}  # comprehensive
        )

    errors = result.get("errors", [])
    assert "MCP_SERVER_UNAVAILABLE" in errors
    assert "WEB_SEARCH_FAILED" in errors

    messages = result.get("messages", [])
    assert messages, "Graph should still produce Agent C output"
    assert "⚠️ 容错降级提示：外部数据源异常..." in str(messages[-1].content)
