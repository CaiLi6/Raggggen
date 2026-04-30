from __future__ import annotations

import pytest

from gateway.request import GatewayRequest
from gateway.response import GatewayResponse
from reports.schema import ReportSource, ResearchReport
from safety.disclosures import default_risk_disclosure
from tools.records import ToolCallRecord


def test_gateway_request_validation() -> None:
    request = GatewayRequest.from_cli("分析 AAPL", output_format="json", mock_tools=True)
    request.validate()
    assert request.normalized_query == "分析 AAPL"
    assert request.metadata["mock_tools"] is True


def test_gateway_request_rejects_empty_query() -> None:
    with pytest.raises(ValueError):
        GatewayRequest(query=" ").validate()


def test_gateway_response_to_dict() -> None:
    report = ResearchReport(
        title="demo",
        query="分析 AAPL",
        thesis=["mock thesis"],
        fundamental="fundamental",
        sentiment="sentiment",
        market_observation="market",
        risks=["risk"],
        missing_data=[],
        next_steps=["step"],
        sources=[ReportSource(source_id="S1", title="source", source_type="mock")],
        disclosure=default_risk_disclosure(),
        trace_id="trace-test",
    )
    record = ToolCallRecord(
        tool_name="mock",
        status="success",
        started_at="t1",
        ended_at="t2",
        elapsed_ms=1,
        input_summary="{}",
    )
    response = GatewayResponse.ok("trace-test", "thread-test", "markdown", report, [record])
    payload = response.to_dict()
    assert payload["report"]["sources"][0]["source_id"] == "S1"
    assert payload["tool_records"][0]["tool_name"] == "mock"
