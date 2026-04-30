"""Gateway response contract."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any

from reports.schema import ResearchReport
from tools.records import ToolCallRecord


def _to_plain(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_plain(item) for key, item in value.items()}
    return value


@dataclass
class GatewayResponse:
    """Unified response object returned to UI, CLI and tests."""

    trace_id: str
    thread_id: str
    markdown: str
    report: ResearchReport | None = None
    tool_records: list[ToolCallRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(
        cls,
        trace_id: str,
        thread_id: str,
        markdown: str,
        report: ResearchReport | None = None,
        tool_records: list[ToolCallRecord] | None = None,
        warnings: list[str] | None = None,
        errors: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "GatewayResponse":
        return cls(
            trace_id=trace_id,
            thread_id=thread_id,
            markdown=markdown,
            report=report,
            tool_records=tool_records or [],
            errors=errors or [],
            warnings=warnings or [],
            metadata=metadata or {},
        )

    @classmethod
    def error(
        cls,
        trace_id: str,
        thread_id: str,
        message: str,
        warnings: list[str] | None = None,
    ) -> "GatewayResponse":
        markdown = (
            "## 请求未能完成\n\n"
            f"- trace_id: `{trace_id}`\n"
            f"- error: {message}\n\n"
            "本系统仅提供研究辅助，不构成投资建议。"
        )
        return cls(
            trace_id=trace_id,
            thread_id=thread_id,
            markdown=markdown,
            errors=[message],
            warnings=warnings or [],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "thread_id": self.thread_id,
            "markdown": self.markdown,
            "report": _to_plain(self.report),
            "tool_records": _to_plain(self.tool_records),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "metadata": _to_plain(self.metadata),
        }
