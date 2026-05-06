"""Integration tests for full agent report flow (task F9)."""

from __future__ import annotations

from gateway.app_gateway import AppGateway
from gateway.request import GatewayRequest
from gateway.response import GatewayResponse
from reports.schema import ResearchReport
from reports.validators import validate_report


def _run_query(query: str, **kwargs) -> GatewayResponse:
    return AppGateway().handle(
        GatewayRequest.from_cli(query=query, mock_tools=True, **kwargs)
    )


def test_full_flow_returns_response() -> None:
    response = _run_query("分析苹果公司的基本面")
    assert isinstance(response, GatewayResponse)


def test_full_flow_no_errors() -> None:
    response = _run_query("分析苹果公司的基本面")
    assert response.errors == []


def test_full_flow_has_report() -> None:
    response = _run_query("分析宁德时代")
    assert response.report is not None
    assert isinstance(response.report, ResearchReport)


def test_full_flow_report_passes_validation() -> None:
    response = _run_query("分析TSLA的竞争优势和风险")
    assert response.report is not None
    errors = validate_report(response.report)
    assert errors == [], f"Validation errors: {errors}"


def test_full_flow_markdown_has_disclaimer() -> None:
    response = _run_query("分析 AAPL")
    assert "不构成投资建议" in response.markdown


def test_full_flow_has_tool_records() -> None:
    response = _run_query("综合分析苹果公司")
    assert len(response.tool_records) >= 2


def test_full_flow_has_trace_id() -> None:
    response = _run_query("q")
    assert response.trace_id.startswith("trace-")


def test_full_flow_has_thread_id() -> None:
    response = _run_query("q", thread_id="integration-test-thread")
    assert response.thread_id == "integration-test-thread"


def test_fundamental_query_uses_rag() -> None:
    response = _run_query("请分析该公司的财报和研报")
    tool_names = [r.tool_name for r in response.tool_records]
    assert "rag_search" in tool_names


def test_sentiment_query_uses_news() -> None:
    response = _run_query("请分析最新的新闻舆情")
    tool_names = [r.tool_name for r in response.tool_records]
    assert "news_search" in tool_names


def test_report_has_sources() -> None:
    response = _run_query("分析宁德时代")
    assert response.report is not None
    assert len(response.report.sources) >= 1


def test_report_has_risks() -> None:
    response = _run_query("分析AAPL风险")
    assert response.report is not None
    assert len(response.report.risks) >= 1
