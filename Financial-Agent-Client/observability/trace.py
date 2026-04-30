"""Execution trace primitives."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from tools.records import ToolCallRecord


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TraceEvent:
    name: str
    started_at: str
    ended_at: str | None = None
    elapsed_ms: int | None = None
    status: str = "started"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionTrace:
    trace_id: str
    thread_id: str
    query: str
    started_at: str = field(default_factory=utc_now_iso)
    ended_at: str | None = None
    elapsed_ms: int | None = None
    events: list[TraceEvent] = field(default_factory=list)
    tool_records: list[ToolCallRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    safety_results: dict[str, Any] = field(default_factory=dict)
    _start_perf: float = field(default_factory=time.perf_counter, repr=False)

    @classmethod
    def start(cls, thread_id: str, query: str) -> "ExecutionTrace":
        return cls(trace_id=f"trace-{uuid.uuid4().hex}", thread_id=thread_id, query=query)

    def event(self, name: str, status: str = "ok", **metadata: Any) -> None:
        now = utc_now_iso()
        self.events.append(
            TraceEvent(
                name=name,
                started_at=now,
                ended_at=now,
                elapsed_ms=0,
                status=status,
                metadata=metadata,
            )
        )

    def add_tool_record(self, record: ToolCallRecord) -> None:
        self.tool_records.append(record)

    def add_warning(self, warning: str) -> None:
        if warning and warning not in self.warnings:
            self.warnings.append(warning)

    def add_error(self, error: str) -> None:
        if error and error not in self.errors:
            self.errors.append(error)

    def finish(self) -> None:
        self.ended_at = utc_now_iso()
        self.elapsed_ms = int((time.perf_counter() - self._start_perf) * 1000)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "thread_id": self.thread_id,
            "query": self.query,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "elapsed_ms": self.elapsed_ms,
            "events": [asdict(event) for event in self.events],
            "tool_records": [asdict(record) for record in self.tool_records],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "safety_results": dict(self.safety_results),
        }
