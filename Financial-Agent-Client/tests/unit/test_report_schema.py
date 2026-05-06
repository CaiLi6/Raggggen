"""Tests for reports/schema.py (task G1)."""

from __future__ import annotations

from dataclasses import asdict

from reports.schema import ReportSource, ResearchReport, RiskDisclosure
from safety.disclosures import default_risk_disclosure


def _make_source() -> ReportSource:
    return ReportSource(
        source_id="S1",
        title="Annual Report 2024",
        source_type="internal_knowledge",
        url=None,
        snippet="Revenue grew 15%",
    )


def _make_report() -> ResearchReport:
    return ResearchReport(
        title="AAPL 研究报告",
        query="分析苹果公司基本面",
        thesis=["苹果公司具备长期竞争优势"],
        fundamental="基本面良好",
        sentiment="情绪中性",
        market_observation="股价稳定",
        risks=["宏观经济风险"],
        missing_data=["最新财报未获取"],
        next_steps=["补充最新财报"],
        sources=[_make_source()],
        disclosure=default_risk_disclosure(),
        trace_id="trace-001",
    )


def test_report_source_creation() -> None:
    source = _make_source()
    assert source.source_id == "S1"
    assert source.title == "Annual Report 2024"
    assert source.source_type == "internal_knowledge"
    assert source.snippet == "Revenue grew 15%"


def test_report_source_url_optional() -> None:
    source = ReportSource(source_id="S2", title="doc", source_type="t")
    assert source.url is None


def test_report_source_metadata_default_empty() -> None:
    source = ReportSource(source_id="S1", title="t", source_type="t")
    assert source.metadata == {}


def test_risk_disclosure_creation() -> None:
    d = RiskDisclosure(
        text="Risk text",
        non_investment_advice="Not investment advice.",
        limitations=["data lag"],
    )
    assert d.text == "Risk text"
    assert d.limitations == ["data lag"]


def test_risk_disclosure_limitations_default_empty() -> None:
    d = RiskDisclosure(text="t", non_investment_advice="n")
    assert d.limitations == []


def test_research_report_creation() -> None:
    report = _make_report()
    assert report.title == "AAPL 研究报告"
    assert report.query == "分析苹果公司基本面"
    assert len(report.thesis) == 1
    assert report.trace_id == "trace-001"


def test_research_report_trace_id_optional() -> None:
    report = _make_report()
    report.trace_id = None
    assert report.trace_id is None


def test_research_report_sources_list() -> None:
    report = _make_report()
    assert len(report.sources) == 1
    assert report.sources[0].source_id == "S1"


def test_report_serializable_as_dict() -> None:
    report = _make_report()
    d = asdict(report)
    assert d["title"] == "AAPL 研究报告"
    assert d["sources"][0]["source_id"] == "S1"
    assert "non_investment_advice" in d["disclosure"]


def test_report_risks_is_list() -> None:
    report = _make_report()
    assert isinstance(report.risks, list)
    assert len(report.risks) == 1


def test_report_missing_data_is_list() -> None:
    report = _make_report()
    assert isinstance(report.missing_data, list)
