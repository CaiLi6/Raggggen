"""Tests for safety/guardrails.py (task D4)."""

from __future__ import annotations

import pytest

from reports.schema import ReportSource, ResearchReport
from safety.disclosures import default_risk_disclosure, NON_INVESTMENT_ADVICE
from safety.guardrails import SafetyGuardrails, SafetyCheckResult
from safety.policy import PROHIBITED_QUERY_PATTERNS


def _make_valid_report() -> ResearchReport:
    return ResearchReport(
        title="AAPL 研究报告",
        query="分析苹果公司基本面",
        thesis=["苹果公司具备长期竞争优势。"],
        fundamental="基本面良好。",
        sentiment="市场情绪中性。",
        market_observation="股价表现平稳。",
        risks=["宏观经济风险", "竞争加剧风险"],
        missing_data=[],
        next_steps=["补充最新财报数据"],
        sources=[ReportSource(source_id="S1", title="研报A", source_type="internal_knowledge")],
        disclosure=default_risk_disclosure(),
    )


def test_validate_clean_query_passes() -> None:
    g = SafetyGuardrails()
    result = g.validate_query("分析苹果公司的基本面")
    assert result.ok is True
    assert result.violations == []


def test_validate_prohibited_query_fails() -> None:
    g = SafetyGuardrails()
    result = g.validate_query("帮我下单买入AAPL")
    assert result.ok is False
    assert len(result.violations) > 0


def test_validate_all_prohibited_patterns_detected() -> None:
    g = SafetyGuardrails()
    for pattern in PROHIBITED_QUERY_PATTERNS:
        result = g.validate_query(f"请{pattern}操作")
        assert result.ok is False, f"Pattern '{pattern}' should be detected"


def test_validate_report_valid_passes() -> None:
    g = SafetyGuardrails()
    report = _make_valid_report()
    result = g.validate_report(report)
    assert result.ok is True
    assert result.violations == []


def test_validate_report_no_sources_adds_warning() -> None:
    g = SafetyGuardrails()
    report = _make_valid_report()
    report.sources = []
    result = g.validate_report(report)
    assert any("source" in w for w in result.warnings)


def test_validate_report_no_risks_adds_warning() -> None:
    g = SafetyGuardrails()
    report = _make_valid_report()
    report.risks = []
    result = g.validate_report(report)
    assert any("risk" in w for w in result.warnings)


def test_validate_report_prohibited_text_fails() -> None:
    g = SafetyGuardrails()
    report = _make_valid_report()
    report.fundamental = "这是保证收益的分析"
    result = g.validate_report(report)
    assert result.ok is False


def test_validate_report_missing_disclaimer_warns() -> None:
    g = SafetyGuardrails()
    report = _make_valid_report()
    report.disclosure.non_investment_advice = "changed text"
    result = g.validate_report(report)
    assert any("non-investment" in w for w in result.warnings)


def test_safety_check_result_is_dataclass() -> None:
    result = SafetyCheckResult(ok=True, violations=[], warnings=["warn1"])
    assert result.ok is True
    assert result.warnings == ["warn1"]
