from __future__ import annotations

import asyncio

from gateway.request import GatewayRequest
from observability.trace import ExecutionTrace
from runtime.graph import FinancialResearchRuntime
from tools.bus import ToolBus
from tools.policy import ToolPolicy


def test_runtime_degrades_when_tools_fail() -> None:
    bus = ToolBus(policy=ToolPolicy(allowed_tools={"rag_search", "news_search", "market_data"}))
    bus.register("rag_search", lambda **kwargs: {"error": "RAG_SERVER_UNAVAILABLE", "chunks": []})
    bus.register("news_search", lambda **kwargs: {"error": "WEB_SEARCH_FAILED", "results": []})
    bus.register("market_data", lambda **kwargs: {"error": "MARKET_DATA_UNAVAILABLE", "snapshot": {}})

    runtime = FinancialResearchRuntime(settings={}, tool_bus=bus)
    request = GatewayRequest.from_cli("请结合财报和舆情分析 TSLA", thread_id="test-degrade")
    trace = ExecutionTrace.start("test-degrade", request.query)
    result = asyncio.run(runtime.run(request, [{"role": "user", "content": request.query}], trace))

    assert result.report is not None
    assert "内部知识库暂未返回足够材料" in result.markdown
    assert "RAG_SERVER_UNAVAILABLE" in [record.error_code for record in result.tool_records]
