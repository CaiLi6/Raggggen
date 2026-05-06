"""Tests for runtime/state.py (task F2)."""

from __future__ import annotations

from context.bundle import ContextBundle
from reports.schema import ResearchReport
from runtime.state import AgentRuntimeState
from safety.disclosures import default_risk_disclosure
from tools.records import ToolCallRecord


def _make_bundle() -> ContextBundle:
    return ContextBundle(
        query="test",
        conversation=[],
        rag_chunks=[],
        news_items=[],
        market_snapshot={},
        source_map={},
        missing_data=[],
        conflicts=[],
        token_budget=6000,
    )


def _make_report() -> ResearchReport:
    return ResearchReport(
        title="T",
        query="q",
        thesis=["t"],
        fundamental="f",
        sentiment="s",
        market_observation="m",
        risks=["r"],
        missing_data=[],
        next_steps=[],
        sources=[],
        disclosure=default_risk_disclosure(),
    )


def test_empty_state_is_typeddict() -> None:
    state: AgentRuntimeState = {}
    assert isinstance(state, dict)


def test_state_can_have_query() -> None:
    state: AgentRuntimeState = {"query": "test query"}
    assert state["query"] == "test query"


def test_state_supports_route_plan() -> None:
    state: AgentRuntimeState = {
        "query": "q",
        "route_intent": "comprehensive",
        "route_plan": ["fundamental", "sentiment", "market_data", "risk", "chief_analyst", "compliance"],
    }
    assert "fundamental" in state["route_plan"]
    assert state["route_intent"] == "comprehensive"


def test_state_supports_tool_outputs() -> None:
    state: AgentRuntimeState = {
        "query": "q",
        "tool_outputs": {"rag_search": {"chunks": []}},
        "tool_records": [],
    }
    assert "rag_search" in state["tool_outputs"]


def test_state_supports_context_bundle() -> None:
    bundle = _make_bundle()
    state: AgentRuntimeState = {"context_bundle": bundle}
    assert state["context_bundle"].query == "test"


def test_state_supports_report() -> None:
    report = _make_report()
    state: AgentRuntimeState = {"report": report}
    assert state["report"].title == "T"


def test_state_supports_warnings_and_errors() -> None:
    state: AgentRuntimeState = {"warnings": ["w1"], "errors": ["e1"]}
    assert state["warnings"] == ["w1"]
    assert state["errors"] == ["e1"]


def test_state_supports_safety_result() -> None:
    state: AgentRuntimeState = {
        "safety_result": {"ok": True, "violations": [], "warnings": []}
    }
    assert state["safety_result"]["ok"] is True
