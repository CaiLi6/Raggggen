"""Tests for agents/compliance_agent.py (task F7)."""

from __future__ import annotations

from reports.schema import ReportSource, ResearchReport
from safety.disclosures import default_risk_disclosure
from safety.guardrails import SafetyGuardrails
from agents.compliance_agent import ComplianceReviewerAgent


def _make_valid_report() -> ResearchReport:
    return ResearchReport(
        title="AAPL Report",
        query="分析苹果公司",
        thesis=["observation"],
        fundamental="fundamental info",
        sentiment="sentiment info",
        market_observation="market info",
        risks=["market risk"],
        missing_data=[],
        next_steps=[],
        sources=[ReportSource(source_id="S1", title="src", source_type="internal_knowledge")],
        disclosure=default_risk_disclosure(),
    )


def test_compliance_agent_sets_safety_result() -> None:
    agent = ComplianceReviewerAgent()
    report = _make_valid_report()
    state = {"report": report}
    updated = agent.run(state)
    assert "safety_result" in updated
    assert "ok" in updated["safety_result"]


def test_compliance_agent_valid_report_ok() -> None:
    agent = ComplianceReviewerAgent()
    report = _make_valid_report()
    state = {"report": report}
    updated = agent.run(state)
    assert updated["safety_result"]["ok"] is True


def test_compliance_agent_prohibited_text_adds_error() -> None:
    agent = ComplianceReviewerAgent()
    report = _make_valid_report()
    report.fundamental = "必须买入，保证收益"
    state = {"report": report}
    updated = agent.run(state)
    assert updated["safety_result"]["ok"] is False
    assert len(updated.get("errors", [])) > 0


def test_compliance_agent_no_sources_adds_warning() -> None:
    agent = ComplianceReviewerAgent()
    report = _make_valid_report()
    report.sources = []
    state = {"report": report}
    updated = agent.run(state)
    assert len(updated.get("warnings", [])) > 0


def test_compliance_agent_appends_to_existing_warnings() -> None:
    agent = ComplianceReviewerAgent()
    report = _make_valid_report()
    report.sources = []
    state = {"report": report, "warnings": ["pre-existing warning"]}
    updated = agent.run(state)
    assert "pre-existing warning" in updated["warnings"]


def test_compliance_agent_uses_custom_guardrails() -> None:
    custom_guardrails = SafetyGuardrails()
    agent = ComplianceReviewerAgent(guardrails=custom_guardrails)
    report = _make_valid_report()
    state = {"report": report}
    updated = agent.run(state)
    assert "safety_result" in updated
