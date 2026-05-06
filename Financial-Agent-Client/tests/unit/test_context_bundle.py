"""Tests for context/bundle.py (task C1)."""

from __future__ import annotations

from context.bundle import ContextBundle


def _make_bundle(**kwargs) -> ContextBundle:
    defaults = dict(
        query="test query",
        conversation=[],
        rag_chunks=[],
        news_items=[],
        market_snapshot={},
        source_map={},
        missing_data=[],
        conflicts=[],
        token_budget=6000,
    )
    defaults.update(kwargs)
    return ContextBundle(**defaults)


def test_bundle_creation() -> None:
    bundle = _make_bundle()
    assert bundle.query == "test query"
    assert bundle.token_budget == 6000


def test_bundle_rag_chunks() -> None:
    chunks = [{"text": "chunk1"}, {"text": "chunk2"}]
    bundle = _make_bundle(rag_chunks=chunks)
    assert len(bundle.rag_chunks) == 2


def test_bundle_news_items() -> None:
    items = [{"title": "news1", "content": "body"}]
    bundle = _make_bundle(news_items=items)
    assert bundle.news_items[0]["title"] == "news1"


def test_bundle_missing_data() -> None:
    bundle = _make_bundle(missing_data=["内部知识库未返回可用材料。"])
    assert len(bundle.missing_data) == 1


def test_bundle_conflicts() -> None:
    bundle = _make_bundle(conflicts=["来源A与来源B结论相悖"])
    assert len(bundle.conflicts) == 1


def test_bundle_source_map() -> None:
    sm = {"S1": {"source_id": "S1", "title": "src"}}
    bundle = _make_bundle(source_map=sm)
    assert "S1" in bundle.source_map


def test_bundle_market_snapshot() -> None:
    snapshot = {"provider": "mock", "symbols": ["AAPL"]}
    bundle = _make_bundle(market_snapshot=snapshot)
    assert bundle.market_snapshot["provider"] == "mock"


def test_bundle_tool_errors_default_empty() -> None:
    bundle = _make_bundle()
    assert bundle.tool_errors == []


def test_bundle_tool_errors_set() -> None:
    bundle = _make_bundle(tool_errors=["RAG_TIMEOUT"])
    assert bundle.tool_errors == ["RAG_TIMEOUT"]


def test_bundle_conversation() -> None:
    conv = [{"role": "user", "content": "q"}]
    bundle = _make_bundle(conversation=conv)
    assert bundle.conversation[0]["role"] == "user"
