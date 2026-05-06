"""E2E tests for golden query set (task I2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gateway.app_gateway import AppGateway
from gateway.request import GatewayRequest
from gateway.response import GatewayResponse
from reports.validators import validate_report


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
GOLDEN_QUERIES_FILE = FIXTURES_DIR / "golden_queries.json"


def load_golden_queries() -> list[dict]:
    with open(GOLDEN_QUERIES_FILE, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.e2e
def test_golden_queries_file_exists() -> None:
    assert GOLDEN_QUERIES_FILE.exists(), f"golden_queries.json not found at {GOLDEN_QUERIES_FILE}"


@pytest.mark.e2e
def test_golden_queries_has_minimum_count() -> None:
    queries = load_golden_queries()
    assert len(queries) >= 20, f"Expected at least 20 golden queries, got {len(queries)}"


@pytest.mark.e2e
def test_golden_queries_all_have_query_field() -> None:
    queries = load_golden_queries()
    for item in queries:
        assert "query" in item, f"Missing 'query' field in item: {item}"
        assert item["query"].strip(), f"Empty query in item: {item}"


@pytest.mark.e2e
@pytest.mark.slow
def test_golden_queries_first_five_produce_valid_reports() -> None:
    """Run the first 5 golden queries with mock tools and validate reports."""
    queries = load_golden_queries()[:5]
    gateway = AppGateway()

    for item in queries:
        query = item["query"]
        response: GatewayResponse = gateway.handle(
            GatewayRequest.from_cli(query=query, mock_tools=True)
        )
        assert response.errors == [], f"Got errors for query '{query}': {response.errors}"
        assert response.report is not None, f"No report for query: {query}"
        validation_errors = validate_report(response.report)
        assert validation_errors == [], (
            f"Report validation failed for query '{query}': {validation_errors}"
        )
        assert "不构成投资建议" in response.markdown, (
            f"Missing disclaimer for query: {query}"
        )


@pytest.mark.e2e
@pytest.mark.slow
def test_golden_queries_all_produce_no_system_crash() -> None:
    """All 20 golden queries should return a response without exceptions."""
    queries = load_golden_queries()
    gateway = AppGateway()
    failures = []

    for item in queries:
        query = item["query"]
        try:
            response = gateway.handle(
                GatewayRequest.from_cli(query=query, mock_tools=True)
            )
            assert response.trace_id.startswith("trace-"), f"Bad trace_id for: {query}"
        except Exception as exc:
            failures.append(f"Query '{query}' raised: {exc}")

    assert not failures, "Golden query failures:\n" + "\n".join(failures)


@pytest.mark.e2e
@pytest.mark.slow
def test_golden_a_stock_queries_return_reports() -> None:
    """A-stock specific queries should produce reports with content."""
    a_stock_queries = [
        "请评估宁德时代短中期投资风险与机会",
        "分析贵州茅台的基本面变化",
        "请分析招商银行基本面和风险",
    ]
    gateway = AppGateway()
    for query in a_stock_queries:
        response = gateway.handle(
            GatewayRequest.from_cli(query=query, mock_tools=True)
        )
        assert response.report is not None, f"No report for A-stock query: {query}"


@pytest.mark.e2e
@pytest.mark.slow
def test_golden_us_stock_queries_return_reports() -> None:
    """US-stock queries should produce reports."""
    us_queries = [
        "分析 AAPL 的基本面和短期情绪",
        "请比较 MSFT 与 NVDA 的风险因素",
        "分析英伟达估值和新闻变化",
    ]
    gateway = AppGateway()
    for query in us_queries:
        response = gateway.handle(
            GatewayRequest.from_cli(query=query, mock_tools=True)
        )
        assert response.report is not None, f"No report for US-stock query: {query}"
