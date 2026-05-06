"""Tests for gateway/response.py (task B2)."""

from __future__ import annotations

from reports.schema import ReportSource, ResearchReport
from safety.disclosures import default_risk_disclosure
from tools.records import ToolCallRecord
from gateway.response import GatewayResponse


def _make_report() -> ResearchReport:
    return ResearchReport(
        title="Test Report",
        query="test query",
        thesis=["thesis point"],
        fundamental="fundamental text",
        sentiment="sentiment text",
        market_observation="market text",
        risks=["risk1"],
        missing_data=[],
        next_steps=["step1"],
        sources=[ReportSource(source_id="S1", title="src", source_type="mock")],
        disclosure=default_risk_disclosure(),
        trace_id="trace-001",
    )


def _make_record() -> ToolCallRecord:
    return ToolCallRecord(
        tool_name="rag_search",
        status="success",
        started_at="t1",
        ended_at="t2",
        elapsed_ms=10,
        input_summary="{}",
        output_summary="ok",
    )


def test_ok_sets_fields() -> None:
    resp = GatewayResponse.ok("trace-1", "thread-1", "# Report")
    assert resp.trace_id == "trace-1"
    assert resp.thread_id == "thread-1"
    assert resp.markdown == "# Report"
    assert resp.errors == []
    assert resp.warnings == []


def test_ok_with_report_and_records() -> None:
    report = _make_report()
    record = _make_record()
    resp = GatewayResponse.ok("t", "th", "md", report=report, tool_records=[record])
    assert resp.report is report
    assert len(resp.tool_records) == 1


def test_error_sets_errors_list() -> None:
    resp = GatewayResponse.error("trace-2", "thread-2", "something went wrong")
    assert len(resp.errors) == 1
    assert "something went wrong" in resp.errors[0]


def test_error_markdown_contains_trace_id() -> None:
    resp = GatewayResponse.error("trace-X", "thread-X", "msg")
    assert "trace-X" in resp.markdown


def test_error_markdown_contains_disclaimer() -> None:
    resp = GatewayResponse.error("t", "th", "err")
    assert "不构成投资建议" in resp.markdown


def test_to_dict_contains_all_keys() -> None:
    resp = GatewayResponse.ok("t", "th", "md")
    d = resp.to_dict()
    for key in ("trace_id", "thread_id", "markdown", "report", "tool_records", "errors", "warnings"):
        assert key in d


def test_to_dict_serializes_report() -> None:
    report = _make_report()
    resp = GatewayResponse.ok("t", "th", "md", report=report)
    d = resp.to_dict()
    assert d["report"]["title"] == "Test Report"
    assert d["report"]["sources"][0]["source_id"] == "S1"


def test_to_dict_serializes_tool_records() -> None:
    record = _make_record()
    resp = GatewayResponse.ok("t", "th", "md", tool_records=[record])
    d = resp.to_dict()
    assert d["tool_records"][0]["tool_name"] == "rag_search"


def test_ok_with_warnings_and_errors() -> None:
    resp = GatewayResponse.ok("t", "th", "md", warnings=["w1"], errors=["e1"])
    assert resp.warnings == ["w1"]
    assert resp.errors == ["e1"]
