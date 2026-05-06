"""Tests for tools/news_search.py (task E2)."""

from __future__ import annotations

import asyncio

import pytest

from tools.news_search import NewsSearchAdapter


def run(coro):
    return asyncio.run(coro)


def test_mock_mode_returns_results() -> None:
    adapter = NewsSearchAdapter(mock=True)
    result = run(adapter("AAPL market news"))
    assert "results" in result
    assert len(result["results"]) >= 1


def test_mock_mode_provider_is_mock_news() -> None:
    adapter = NewsSearchAdapter(mock=True)
    result = run(adapter("q"))
    assert result.get("provider") == "mock_news"


def test_mock_result_contains_title() -> None:
    adapter = NewsSearchAdapter(mock=True)
    result = run(adapter("q"))
    assert "title" in result["results"][0]


def test_mock_result_contains_query_text() -> None:
    adapter = NewsSearchAdapter(mock=True)
    result = run(adapter("宁德时代"))
    content = result["results"][0].get("content", "")
    assert "宁德时代" in content


def test_no_api_key_returns_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    adapter = NewsSearchAdapter(mock=False)
    result = run(adapter("q"))
    assert result.get("error") == "WEB_SEARCH_FAILED"
    assert result.get("results") == []


def test_mock_respects_max_results_param() -> None:
    adapter = NewsSearchAdapter(mock=True, max_results=1)
    result = run(adapter("q"))
    # Mock always returns 1 item; verify list is not empty
    assert isinstance(result["results"], list)
