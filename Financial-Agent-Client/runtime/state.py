"""Runtime state contracts."""

from __future__ import annotations

from typing import Any, TypedDict

from context.bundle import ContextBundle
from reports.schema import ResearchReport
from tools.records import ToolCallRecord


class AgentRuntimeState(TypedDict, total=False):
    query: str
    thread_id: str
    collection: str | None
    route_intent: str
    route_plan: list[str]
    conversation: list[dict[str, str]]
    tool_outputs: dict[str, Any]
    tool_records: list[ToolCallRecord]
    context_bundle: ContextBundle
    risk_findings: list[str]
    report: ResearchReport
    markdown: str
    warnings: list[str]
    errors: list[str]
    safety_result: dict[str, Any]
