"""Tests for tools/records.py (task D2)."""

from __future__ import annotations

from tools.records import ToolCallRecord, utc_now_iso


def test_utc_now_iso_returns_string() -> None:
    ts = utc_now_iso()
    assert isinstance(ts, str)
    assert "T" in ts


def test_utc_now_iso_contains_utc_offset() -> None:
    ts = utc_now_iso()
    assert "+" in ts or "Z" in ts or ts.endswith("+00:00")


def test_tool_call_record_success() -> None:
    record = ToolCallRecord(
        tool_name="rag_search",
        status="success",
        started_at="2024-01-01T00:00:00+00:00",
        ended_at="2024-01-01T00:00:01+00:00",
        elapsed_ms=1000,
        input_summary='{"query": "test"}',
        output_summary="ok",
    )
    assert record.tool_name == "rag_search"
    assert record.status == "success"
    assert record.elapsed_ms == 1000
    assert record.output_summary == "ok"
    assert record.error_code is None
    assert record.error_message is None


def test_tool_call_record_error() -> None:
    record = ToolCallRecord(
        tool_name="news_search",
        status="error",
        started_at="2024-01-01T00:00:00+00:00",
        ended_at="2024-01-01T00:00:01+00:00",
        elapsed_ms=100,
        input_summary="{}",
        error_code="WEB_SEARCH_FAILED",
        error_message="connection refused",
    )
    assert record.status == "error"
    assert record.error_code == "WEB_SEARCH_FAILED"
    assert record.error_message == "connection refused"


def test_tool_call_record_defaults() -> None:
    record = ToolCallRecord(
        tool_name="market_data",
        status="success",
        started_at="t1",
        ended_at="t2",
        elapsed_ms=5,
        input_summary="{}",
    )
    assert record.output_summary is None
    assert record.error_code is None
    assert record.error_message is None
    assert record.role is None


def test_tool_call_record_with_role() -> None:
    record = ToolCallRecord(
        tool_name="rag_search",
        status="success",
        started_at="t1",
        ended_at="t2",
        elapsed_ms=1,
        input_summary="{}",
        role="fundamental",
    )
    assert record.role == "fundamental"
