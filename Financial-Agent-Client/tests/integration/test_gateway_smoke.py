from __future__ import annotations

from gateway.app_gateway import AppGateway
from gateway.request import GatewayRequest


def test_gateway_mock_smoke_returns_report() -> None:
    response = AppGateway().handle(
        GatewayRequest.from_cli(
            query="请结合财报和舆情分析 TSLA",
            thread_id="test-gateway",
            mock_tools=True,
            enable_eval=True,
        )
    )

    assert response.errors == []
    assert response.report is not None
    assert response.report.sources
    assert "不构成投资建议" in response.markdown
    assert len(response.tool_records) >= 3
    assert response.metadata["evaluation"]["overall"] >= 0
