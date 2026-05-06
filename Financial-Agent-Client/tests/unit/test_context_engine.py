"""Tests for context/engine.py (task C3)."""

from __future__ import annotations

from context.bundle import ContextBundle
from context.engine import ContextEngine
from tools.records import ToolCallRecord


def _make_error_record(name: str, code: str) -> ToolCallRecord:
    return ToolCallRecord(
        tool_name=name,
        status="error",
        started_at="t1",
        ended_at="t2",
        elapsed_ms=10,
        input_summary="{}",
        error_code=code,
        error_message="failed",
    )


def _make_success_record(name: str) -> ToolCallRecord:
    return ToolCallRecord(
        tool_name=name,
        status="success",
        started_at="t1",
        ended_at="t2",
        elapsed_ms=10,
        input_summary="{}",
    )


def test_build_returns_context_bundle() -> None:
    engine = ContextEngine()
    bundle = engine.build("test query", [], {}, [])
    assert isinstance(bundle, ContextBundle)


def test_build_sets_query() -> None:
    engine = ContextEngine()
    bundle = engine.build("my query", [], {}, [])
    assert bundle.query == "my query"


def test_build_normalizes_rag_chunks() -> None:
    engine = ContextEngine()
    rag_data = {
        "provider": "rag_mcp",
        "chunks": [
            {"title": "Doc A", "text": "Content A"},
            {"title": "Doc B", "text": "Content B"},
        ],
    }
    bundle = engine.build("q", [], {"rag_search": rag_data}, [])
    assert len(bundle.rag_chunks) == 2
    assert bundle.rag_chunks[0]["source_id"] == "S1"


def test_build_normalizes_news_items() -> None:
    engine = ContextEngine()
    news_data = {
        "provider": "mock_news",
        "results": [{"title": "News 1", "url": "http://n1.com", "content": "body"}],
    }
    bundle = engine.build("q", [], {"news_search": news_data}, [])
    assert len(bundle.news_items) == 1
    assert "source_id" in bundle.news_items[0]


def test_build_normalizes_market_snapshot() -> None:
    engine = ContextEngine()
    market_data = {"snapshot": {"provider": "mock", "symbols": ["AAPL"]}}
    bundle = engine.build("q", [], {"market_data": market_data}, [])
    assert bundle.market_snapshot.get("provider") == "mock"


def test_build_missing_rag_adds_to_missing_data() -> None:
    engine = ContextEngine()
    bundle = engine.build("q", [], {}, [])
    assert any("知识库" in m for m in bundle.missing_data)


def test_build_missing_news_adds_to_missing_data() -> None:
    engine = ContextEngine()
    bundle = engine.build("q", [], {}, [])
    assert any("新闻" in m for m in bundle.missing_data)


def test_build_missing_market_adds_to_missing_data() -> None:
    engine = ContextEngine()
    bundle = engine.build("q", [], {}, [])
    assert any("行情" in m for m in bundle.missing_data)


def test_build_tool_error_records_added() -> None:
    engine = ContextEngine()
    records = [_make_error_record("rag_search", "RAG_TIMEOUT")]
    bundle = engine.build("q", [], {}, records)
    assert len(bundle.tool_errors) == 1
    assert "RAG_TIMEOUT" in bundle.tool_errors[0]


def test_build_success_records_not_added_to_errors() -> None:
    engine = ContextEngine()
    records = [_make_success_record("rag_search")]
    bundle = engine.build("q", [], {}, records)
    assert bundle.tool_errors == []


def test_build_truncates_conversation_to_8() -> None:
    engine = ContextEngine()
    conv = [{"role": "user", "content": f"msg{i}"} for i in range(12)]
    bundle = engine.build("q", conv, {}, [])
    assert len(bundle.conversation) == 8


def test_build_source_map_populated() -> None:
    engine = ContextEngine()
    rag_data = {"chunks": [{"title": "A", "text": "x"}]}
    bundle = engine.build("q", [], {"rag_search": rag_data}, [])
    assert len(bundle.source_map) >= 1


def test_custom_token_budget() -> None:
    engine = ContextEngine(token_budget=2000)
    bundle = engine.build("q", [], {}, [])
    assert bundle.token_budget == 2000
