"""Integration tests for Runtime + Tool Bus (task E4)."""

from __future__ import annotations

import asyncio

from tools import create_default_tool_bus
from tools.bus import ToolBus
from tools.policy import ToolPolicy


def run(coro):
    return asyncio.run(coro)


def test_default_tool_bus_registers_expected_tools() -> None:
    bus = create_default_tool_bus(mock_tools=True)
    tools = bus.list_tools()
    assert "rag_search" in tools
    assert "news_search" in tools
    assert "market_data" in tools
    assert "evaluate_report" in tools


def test_rag_search_via_bus_mock() -> None:
    bus = create_default_tool_bus(mock_tools=True)
    result = run(bus.call("rag_search", {"query": "AAPL财报"}))
    assert result.record.status == "success"
    assert "chunks" in result.data


def test_news_search_via_bus_mock() -> None:
    bus = create_default_tool_bus(mock_tools=True)
    result = run(bus.call("news_search", {"query": "市场新闻"}))
    assert result.record.status == "success"
    assert "results" in result.data


def test_market_data_via_bus() -> None:
    bus = create_default_tool_bus(mock_tools=True)
    result = run(bus.call("market_data", {"query": "TSLA股价"}))
    assert result.record.status == "success"
    assert "snapshot" in result.data


def test_evaluate_report_via_bus() -> None:
    bus = create_default_tool_bus(mock_tools=True)
    result = run(bus.call(
        "evaluate_report",
        {"query": "q", "report_markdown": "# Report\n风险\n不构成投资建议"},
    ))
    assert result.record.status == "success"
    assert "overall" in result.data


def test_denied_tool_returns_policy_denied_error() -> None:
    bus = create_default_tool_bus(mock_tools=True)

    async def fake_handler(**kwargs):
        return {}

    bus.register("broker_order", fake_handler)
    result = run(bus.call("broker_order", {}))
    assert result.record.status == "error"
    assert result.record.error_code == "POLICY_DENIED"


def test_bus_records_are_stored() -> None:
    bus = create_default_tool_bus(mock_tools=True)
    run(bus.call("rag_search", {"query": "q"}))
    run(bus.call("news_search", {"query": "q"}))
    assert len(bus.records) == 2


def test_bus_records_contain_tool_names() -> None:
    bus = create_default_tool_bus(mock_tools=True)
    run(bus.call("rag_search", {"query": "q"}))
    assert bus.records[0].tool_name == "rag_search"


def test_unknown_tool_returns_error_record() -> None:
    bus = create_default_tool_bus(mock_tools=True)
    result = run(bus.call("nonexistent_tool", {}))
    assert result.record.status == "error"
    assert result.record.error_code is not None
