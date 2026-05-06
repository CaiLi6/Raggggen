"""Tests for reports/validators.py (task G3)."""

from __future__ import annotations

from reports.schema import ReportSource, ResearchReport
from reports.validators import validate_report
from safety.disclosures import default_risk_disclosure, NON_INVESTMENT_ADVICE


def _make_valid_report() -> ResearchReport:
    return ResearchReport(
        title="Test Report",
        query="分析苹果公司",
        thesis=["thesis point"],
        fundamental="fundamental",
        sentiment="sentiment",
        market_observation="market",
        risks=["risk1"],
        missing_data=[],
        next_steps=[],
        sources=[ReportSource(source_id="S1", title="src", source_type="mock")],
        disclosure=default_risk_disclosure(),
    )


def test_valid_report_no_errors() -> None:
    report = _make_valid_report()
    errors = validate_report(report)
    assert errors == []


def test_empty_query_error() -> None:
    report = _make_valid_report()
    report.query = "   "
    errors = validate_report(report)
    assert any("query" in e for e in errors)


def test_empty_thesis_error() -> None:
    report = _make_valid_report()
    report.thesis = []
    errors = validate_report(report)
    assert any("thesis" in e for e in errors)


def test_empty_risks_error() -> None:
    report = _make_valid_report()
    report.risks = []
    errors = validate_report(report)
    assert any("risk" in e for e in errors)


def test_empty_sources_error() -> None:
    report = _make_valid_report()
    report.sources = []
    errors = validate_report(report)
    assert any("source" in e for e in errors)


def test_missing_disclosure_error() -> None:
    report = _make_valid_report()
    report.disclosure.non_investment_advice = "some other text"
    errors = validate_report(report)
    assert any("non-investment" in e for e in errors)


def test_valid_disclosure_no_error() -> None:
    report = _make_valid_report()
    assert NON_INVESTMENT_ADVICE in report.disclosure.non_investment_advice
    errors = validate_report(report)
    disclosure_errors = [e for e in errors if "non-investment" in e]
    assert disclosure_errors == []


def test_multiple_errors_returned() -> None:
    report = _make_valid_report()
    report.query = ""
    report.thesis = []
    report.risks = []
    report.sources = []
    errors = validate_report(report)
    assert len(errors) >= 4
