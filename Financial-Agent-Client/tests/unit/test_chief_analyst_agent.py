"""Tests for agents/chief_analyst_agent.py (task F8)."""

from __future__ import annotations

from context.bundle import ContextBundle
from agents.chief_analyst_agent import ChiefAnalystAgent
from reports.schema import ResearchReport


def _make_bundle(
    rag_chunks: list | None = None,
    news_items: list | None = None,
    market_snapshot: dict | None = None,
    missing_data: list | None = None,
) -> ContextBundle:
    return ContextBundle(
        query="分析宁德时代的竞争优势",
        conversation=[],
        rag_chunks=rag_chunks or [],
        news_items=news_items or [],
        market_snapshot=market_snapshot or {},
        source_map={"S1": {"source_id": "S1", "title": "src", "source_type": "internal_knowledge"}},
        missing_data=missing_data or [],
        conflicts=[],
        token_budget=6000,
    )


def test_chief_analyst_returns_report_in_state() -> None:
    agent = ChiefAnalystAgent()
    bundle = _make_bundle()
    state = {"context_bundle": bundle, "risk_findings": ["risk1"]}
    updated = agent.run(state)
    assert "report" in updated
    assert isinstance(updated["report"], ResearchReport)


def test_report_title_contains_query_prefix() -> None:
    agent = ChiefAnalystAgent()
    bundle = _make_bundle()
    state = {"context_bundle": bundle, "risk_findings": []}
    updated = agent.run(state)
    assert "分析宁德时代" in updated["report"].title


def test_report_query_matches_bundle_query() -> None:
    agent = ChiefAnalystAgent()
    bundle = _make_bundle()
    state = {"context_bundle": bundle, "risk_findings": []}
    updated = agent.run(state)
    assert updated["report"].query == bundle.query


def test_report_risks_from_risk_findings() -> None:
    agent = ChiefAnalystAgent()
    bundle = _make_bundle()
    state = {"context_bundle": bundle, "risk_findings": ["市场风险", "流动性风险"]}
    updated = agent.run(state)
    assert "市场风险" in updated["report"].risks


def test_report_has_disclosure() -> None:
    agent = ChiefAnalystAgent()
    bundle = _make_bundle()
    state = {"context_bundle": bundle, "risk_findings": []}
    updated = agent.run(state)
    assert updated["report"].disclosure is not None
    assert updated["report"].disclosure.non_investment_advice


def test_report_thesis_with_rag_data() -> None:
    agent = ChiefAnalystAgent()
    bundle = _make_bundle(rag_chunks=[{"title": "doc", "text": "content", "source_id": "S1"}])
    state = {"context_bundle": bundle, "risk_findings": []}
    updated = agent.run(state)
    thesis_text = " ".join(updated["report"].thesis)
    assert "内部知识库" in thesis_text


def test_report_thesis_without_rag_data_notes_lack() -> None:
    agent = ChiefAnalystAgent()
    bundle = _make_bundle(rag_chunks=[])
    state = {"context_bundle": bundle, "risk_findings": []}
    updated = agent.run(state)
    thesis_text = " ".join(updated["report"].thesis)
    assert "内部知识库" in thesis_text


def test_report_missing_data_from_bundle() -> None:
    agent = ChiefAnalystAgent()
    bundle = _make_bundle(missing_data=["行情摘要不可用。"])
    state = {"context_bundle": bundle, "risk_findings": []}
    updated = agent.run(state)
    assert "行情摘要不可用。" in updated["report"].missing_data
