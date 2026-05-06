"""Tests for agents/sentiment_agent.py (task F5)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from agents.sentiment_agent import SentimentAnalystAgent
from tools.bus import ToolBus, ToolExecutionResult
from tools.records import ToolCallRecord


def _make_mock_bus(data: dict, status: str = "success") -> ToolBus:
    record = ToolCallRecord(
        tool_name="news_search",
        status=status,
        started_at="t1",
        ended_at="t2",
        elapsed_ms=5,
        input_summary="{}",
    )
    result = ToolExecutionResult(data=data, record=record)
    bus = MagicMock(spec=ToolBus)
    bus.call = AsyncMock(return_value=result)
    return bus


def run(coro):
    return asyncio.run(coro)


def test_sentiment_agent_calls_news_search() -> None:
    agent = SentimentAnalystAgent()
    bus = _make_mock_bus({"results": []})
    state = {"query": "最新新闻"}
    run(agent.run(state, bus))
    bus.call.assert_called_once()
    assert bus.call.call_args[0][0] == "news_search"


def test_sentiment_agent_sets_news_in_tool_outputs() -> None:
    agent = SentimentAnalystAgent()
    news_data = {"results": [{"title": "news1"}]}
    bus = _make_mock_bus(news_data)
    state = {"query": "q"}
    updated = run(agent.run(state, bus))
    assert updated["tool_outputs"]["news_search"] is news_data


def test_sentiment_agent_adds_tool_record() -> None:
    agent = SentimentAnalystAgent()
    bus = _make_mock_bus({"results": []})
    state = {"query": "q"}
    updated = run(agent.run(state, bus))
    assert len(updated["tool_records"]) == 1
    assert updated["tool_records"][0].tool_name == "news_search"


def test_sentiment_agent_passes_query() -> None:
    agent = SentimentAnalystAgent()
    bus = _make_mock_bus({})
    state = {"query": "苹果新闻"}
    run(agent.run(state, bus))
    call_kwargs = bus.call.call_args[0][1]
    assert call_kwargs["query"] == "苹果新闻"


def test_sentiment_agent_error_record_stored() -> None:
    agent = SentimentAnalystAgent()
    bus = _make_mock_bus({"error": "WEB_SEARCH_FAILED", "results": []}, status="error")
    state = {"query": "q"}
    updated = run(agent.run(state, bus))
    assert updated["tool_records"][0].status == "error"
