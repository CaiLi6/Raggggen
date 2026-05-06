"""Tests for agents/risk_agent.py (task F6)."""

from __future__ import annotations

from context.bundle import ContextBundle
from agents.risk_agent import RiskAnalystAgent


def _make_bundle(
    tool_errors: list[str] | None = None,
    missing_data: list[str] | None = None,
) -> ContextBundle:
    return ContextBundle(
        query="test",
        conversation=[],
        rag_chunks=[],
        news_items=[],
        market_snapshot={},
        source_map={},
        missing_data=missing_data or [],
        conflicts=[],
        token_budget=6000,
        tool_errors=tool_errors or [],
    )


def test_risk_agent_sets_risk_findings() -> None:
    agent = RiskAnalystAgent()
    bundle = _make_bundle()
    state = {"context_bundle": bundle}
    updated = agent.run(state)
    assert "risk_findings" in updated
    assert len(updated["risk_findings"]) >= 2


def test_risk_agent_includes_default_risks() -> None:
    agent = RiskAnalystAgent()
    bundle = _make_bundle()
    state = {"context_bundle": bundle}
    updated = agent.run(state)
    risks_text = " ".join(updated["risk_findings"])
    assert "风险" in risks_text


def test_risk_agent_includes_tool_errors() -> None:
    agent = RiskAnalystAgent()
    bundle = _make_bundle(tool_errors=["RAG_TIMEOUT"])
    state = {"context_bundle": bundle}
    updated = agent.run(state)
    risks_text = " ".join(updated["risk_findings"])
    assert "RAG_TIMEOUT" in risks_text


def test_risk_agent_includes_missing_data() -> None:
    agent = RiskAnalystAgent()
    bundle = _make_bundle(missing_data=["内部知识库未返回可用材料。"])
    state = {"context_bundle": bundle}
    updated = agent.run(state)
    assert "内部知识库未返回可用材料。" in updated["risk_findings"]


def test_risk_agent_no_errors_two_default_risks() -> None:
    agent = RiskAnalystAgent()
    bundle = _make_bundle()
    state = {"context_bundle": bundle}
    updated = agent.run(state)
    assert len(updated["risk_findings"]) == 2


def test_risk_agent_multiple_tool_errors() -> None:
    agent = RiskAnalystAgent()
    bundle = _make_bundle(tool_errors=["RAG_TIMEOUT", "WEB_SEARCH_FAILED"])
    state = {"context_bundle": bundle}
    updated = agent.run(state)
    risks_text = " ".join(updated["risk_findings"])
    assert "RAG_TIMEOUT" in risks_text
    assert "WEB_SEARCH_FAILED" in risks_text
