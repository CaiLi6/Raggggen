"""Tests for observability/trace.py - trace events (task H3)."""

from __future__ import annotations

from observability.trace import ExecutionTrace, TraceEvent
from tools.records import ToolCallRecord


def test_execution_trace_start() -> None:
    trace = ExecutionTrace.start(thread_id="t1", query="test query")
    assert trace.thread_id == "t1"
    assert trace.query == "test query"
    assert trace.trace_id.startswith("trace-")


def test_execution_trace_unique_ids() -> None:
    ids = {ExecutionTrace.start("t", "q").trace_id for _ in range(10)}
    assert len(ids) == 10


def test_trace_event_added() -> None:
    trace = ExecutionTrace.start("t", "q")
    trace.event("router_start", status="ok", agent="router")
    assert len(trace.events) == 1
    assert trace.events[0].name == "router_start"
    assert trace.events[0].status == "ok"


def test_trace_multiple_events() -> None:
    trace = ExecutionTrace.start("t", "q")
    trace.event("router_start")
    trace.event("fundamental_done")
    assert len(trace.events) == 2
    assert trace.events[1].name == "fundamental_done"


def test_add_tool_record() -> None:
    trace = ExecutionTrace.start("t", "q")
    record = ToolCallRecord(
        tool_name="rag_search",
        status="success",
        started_at="t1",
        ended_at="t2",
        elapsed_ms=100,
        input_summary="{}",
    )
    trace.add_tool_record(record)
    assert len(trace.tool_records) == 1
    assert trace.tool_records[0].tool_name == "rag_search"


def test_add_warning() -> None:
    trace = ExecutionTrace.start("t", "q")
    trace.add_warning("low source count")
    assert "low source count" in trace.warnings


def test_add_warning_deduplicates() -> None:
    trace = ExecutionTrace.start("t", "q")
    trace.add_warning("same warning")
    trace.add_warning("same warning")
    assert trace.warnings.count("same warning") == 1


def test_add_error() -> None:
    trace = ExecutionTrace.start("t", "q")
    trace.add_error("RAG_TIMEOUT")
    assert "RAG_TIMEOUT" in trace.errors


def test_add_error_deduplicates() -> None:
    trace = ExecutionTrace.start("t", "q")
    trace.add_error("err")
    trace.add_error("err")
    assert trace.errors.count("err") == 1


def test_finish_sets_ended_at_and_elapsed_ms() -> None:
    trace = ExecutionTrace.start("t", "q")
    trace.finish()
    assert trace.ended_at is not None
    assert isinstance(trace.elapsed_ms, int)
    assert trace.elapsed_ms >= 0


def test_to_dict_contains_all_keys() -> None:
    trace = ExecutionTrace.start("t", "q")
    trace.finish()
    d = trace.to_dict()
    for key in ("trace_id", "thread_id", "query", "started_at", "ended_at", "elapsed_ms",
                "events", "tool_records", "warnings", "errors", "safety_results"):
        assert key in d


def test_to_dict_events_are_serializable() -> None:
    trace = ExecutionTrace.start("t", "q")
    trace.event("test_event", status="ok")
    d = trace.to_dict()
    assert len(d["events"]) == 1
    assert d["events"][0]["name"] == "test_event"


def test_trace_event_dataclass() -> None:
    evt = TraceEvent(
        name="test",
        started_at="2024-01-01T00:00:00+00:00",
        ended_at="2024-01-01T00:00:01+00:00",
        elapsed_ms=1000,
        status="ok",
        metadata={"agent": "router"},
    )
    assert evt.name == "test"
    assert evt.metadata["agent"] == "router"
