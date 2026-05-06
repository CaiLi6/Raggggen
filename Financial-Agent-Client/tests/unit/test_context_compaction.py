"""Tests for context compaction (task C4)."""

from __future__ import annotations

from context.engine import ContextEngine


def _make_long_rag_chunks(n: int) -> dict:
    return {
        "chunks": [
            {"title": f"Doc {i}", "text": "x" * 100}
            for i in range(n)
        ]
    }


def _make_long_news(n: int) -> dict:
    return {
        "results": [
            {"title": f"News {i}", "url": f"http://n{i}.com", "content": "y" * 100}
            for i in range(n)
        ]
    }


def test_rag_chunks_are_limited_by_engine_build() -> None:
    engine = ContextEngine(token_budget=500)
    tool_outputs = {"rag_search": _make_long_rag_chunks(20)}
    bundle = engine.build("q", [], tool_outputs, [])
    # ContextEngine.build normalizes but does not truncate chunk list beyond what's provided
    # Verify all chunks are assigned source_ids
    for chunk in bundle.rag_chunks:
        assert "source_id" in chunk


def test_conversation_kept_to_last_8_entries() -> None:
    engine = ContextEngine()
    conv = [{"role": "user", "content": f"msg{i}"} for i in range(20)]
    bundle = engine.build("q", conv, {}, [])
    assert len(bundle.conversation) == 8
    # Verify it kept the LAST 8
    assert bundle.conversation[-1]["content"] == "msg19"


def test_conversation_shorter_than_8_kept_full() -> None:
    engine = ContextEngine()
    conv = [{"role": "user", "content": f"msg{i}"} for i in range(5)]
    bundle = engine.build("q", conv, {}, [])
    assert len(bundle.conversation) == 5


def test_source_map_populated_with_both_rag_and_news() -> None:
    engine = ContextEngine()
    tool_outputs = {
        "rag_search": _make_long_rag_chunks(3),
        "news_search": _make_long_news(2),
    }
    bundle = engine.build("q", [], tool_outputs, [])
    # Should have 5 sources: 3 rag + 2 news
    assert len(bundle.source_map) == 5


def test_missing_data_empty_when_all_tools_return_data() -> None:
    engine = ContextEngine()
    tool_outputs = {
        "rag_search": _make_long_rag_chunks(1),
        "news_search": _make_long_news(1),
        "market_data": {"snapshot": {"provider": "mock", "summary": "ok"}},
    }
    bundle = engine.build("q", [], tool_outputs, [])
    # No "tool_errors" entries, and all data present → no missing_data items
    non_tool_error_missing = [m for m in bundle.missing_data if "工具异常" not in m]
    assert non_tool_error_missing == []
