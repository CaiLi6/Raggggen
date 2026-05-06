"""Tool call audit record contract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ToolCallRecord:
    tool_name: str
    status: Literal["success", "error"]
    started_at: str
    ended_at: str
    elapsed_ms: int
    input_summary: str
    output_summary: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    role: str | None = None
    attempt_count: int = 1
