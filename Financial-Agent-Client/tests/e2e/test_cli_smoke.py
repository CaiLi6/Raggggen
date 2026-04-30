from __future__ import annotations

from scripts.main import run_once


def test_cli_run_once_mock_tools() -> None:
    response = run_once("分析 AAPL 的基本面和舆情", thread_id="test-cli", mock_tools=True)
    assert response.errors == []
    assert response.trace_id.startswith("trace-")
    assert "AAPL" in response.markdown
