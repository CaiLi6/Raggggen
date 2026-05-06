"""Tests for agents/fundamental_agent.py (task F4)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from agents.fundamental_agent import FundamentalAnalystAgent
from tools.bus import ToolBus, ToolExecutionResult
from tools.records import ToolCallRecord


def _make_mock_bus(data: dict, status: str = "success") -> ToolBus:
    record = ToolCallRecord(
        tool_name="rag_search",
        status=status,
        started_at="t1",
        ended_at="t2",
        elapsed_ms=10,
        input_summary="{}",
    )
    result = ToolExecutionResult(data=data, record=record)
    bus = MagicMock(spec=ToolBus)
    bus.call = AsyncMock(return_value=result)
    return bus


def run(coro):
    return asyncio.run(coro)


def test_fundamental_agent_calls_rag_search() -> None:
    agent = FundamentalAnalystAgent()
    bus = _make_mock_bus({"chunks": [{"title": "doc", "text": "content"}]})
    state = {"query": "分析AAPL", "collection": "default"}
    run(agent.run(state, bus))
    bus.call.assert_called_once()
    call_args = bus.call.call_args
    assert call_args[0][0] == "rag_search"


def test_fundamental_agent_sets_tool_outputs() -> None:
    agent = FundamentalAnalystAgent()
    rag_data = {"chunks": [{"title": "doc", "text": "content"}]}
    bus = _make_mock_bus(rag_data)
    state = {"query": "q"}
    updated = run(agent.run(state, bus))
    assert "rag_search" in updated["tool_outputs"]
    assert updated["tool_outputs"]["rag_search"] is rag_data


def test_fundamental_agent_adds_tool_record() -> None:
    agent = FundamentalAnalystAgent()
    bus = _make_mock_bus({"chunks": []})
    state = {"query": "q"}
    updated = run(agent.run(state, bus))
    assert len(updated["tool_records"]) == 1
    assert updated["tool_records"][0].tool_name == "rag_search"


def test_fundamental_agent_passes_query_to_rag() -> None:
    agent = FundamentalAnalystAgent()
    bus = _make_mock_bus({})
    state = {"query": "宁德时代财报"}
    run(agent.run(state, bus))
    call_kwargs = bus.call.call_args[0][1]
    assert call_kwargs["query"] == "宁德时代财报"


def test_fundamental_agent_passes_collection() -> None:
    agent = FundamentalAnalystAgent()
    bus = _make_mock_bus({})
    state = {"query": "q", "collection": "finance_reports"}
    run(agent.run(state, bus))
    call_kwargs = bus.call.call_args[0][1]
    assert call_kwargs["collection"] == "finance_reports"
