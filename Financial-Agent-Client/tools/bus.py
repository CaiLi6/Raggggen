"""Unified Tool Bus with policy checks and audit records."""

from __future__ import annotations

import asyncio
import inspect
import json
import time
from dataclasses import dataclass
from typing import Any, Callable

from tools.policy import ToolPolicy
from tools.records import ToolCallRecord, utc_now_iso


ToolHandler = Callable[..., Any]


@dataclass
class ToolExecutionResult:
    data: Any
    record: ToolCallRecord


def _summarize(value: Any, limit: int = 500) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        text = str(value)
    return text[:limit]


class ToolBus:
    """Single audited entry point for all tool calls."""

    def __init__(self, policy: ToolPolicy | None = None):
        self.policy = policy or ToolPolicy()
        self._handlers: dict[str, ToolHandler] = {}
        self.records: list[ToolCallRecord] = []

    def register(self, name: str, handler: ToolHandler) -> None:
        self._handlers[name] = handler

    def list_tools(self) -> list[str]:
        return sorted(self._handlers)

    async def call(
        self,
        name: str,
        args: dict[str, Any] | None = None,
        role: str | None = None,
        timeout_seconds: float | None = None,
    ) -> ToolExecutionResult:
        args = args or {}
        started_at = utc_now_iso()
        start = time.perf_counter()

        if not self.policy.is_allowed(name):
            record = self._record(
                name=name,
                role=role,
                started_at=started_at,
                start=start,
                status="error",
                input_summary=_summarize(args),
                error_code="POLICY_DENIED",
                error_message=f"Tool '{name}' is denied by policy",
            )
            return ToolExecutionResult(data={"error": "POLICY_DENIED", "message": record.error_message}, record=record)

        handler = self._handlers.get(name)
        if handler is None:
            record = self._record(
                name=name,
                role=role,
                started_at=started_at,
                start=start,
                status="error",
                input_summary=_summarize(args),
                error_code="TOOL_NOT_REGISTERED",
                error_message=f"Tool '{name}' is not registered",
            )
            return ToolExecutionResult(data={"error": "TOOL_NOT_REGISTERED", "message": record.error_message}, record=record)

        try:
            data = await self._invoke(handler, args, timeout_seconds=timeout_seconds)
            status = "error" if isinstance(data, dict) and data.get("error") else "success"
            record = self._record(
                name=name,
                role=role,
                started_at=started_at,
                start=start,
                status=status,
                input_summary=_summarize(args),
                output_summary=_summarize(data),
                error_code=str(data.get("error")) if isinstance(data, dict) and data.get("error") else None,
                error_message=str(data.get("message")) if isinstance(data, dict) and data.get("message") else None,
            )
            return ToolExecutionResult(data=data, record=record)
        except TimeoutError as exc:
            record = self._record(
                name=name,
                role=role,
                started_at=started_at,
                start=start,
                status="error",
                input_summary=_summarize(args),
                error_code=f"{name.upper()}_TIMEOUT",
                error_message=str(exc) or "tool timed out",
            )
            return ToolExecutionResult(data={"error": record.error_code, "message": record.error_message}, record=record)
        except Exception as exc:
            record = self._record(
                name=name,
                role=role,
                started_at=started_at,
                start=start,
                status="error",
                input_summary=_summarize(args),
                error_code="UNKNOWN_ERROR",
                error_message=str(exc),
            )
            return ToolExecutionResult(data={"error": "UNKNOWN_ERROR", "message": str(exc)}, record=record)

    async def _invoke(
        self,
        handler: ToolHandler,
        args: dict[str, Any],
        timeout_seconds: float | None,
    ) -> Any:
        call_method = getattr(handler, "__call__", None)
        is_async_callable = inspect.iscoroutinefunction(handler) or inspect.iscoroutinefunction(call_method)
        if is_async_callable:
            coro = handler(**args)
        else:
            coro = asyncio.to_thread(handler, **args)
        if timeout_seconds:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        result = await coro
        if inspect.isawaitable(result):
            return await result
        return result

    def _record(
        self,
        name: str,
        role: str | None,
        started_at: str,
        start: float,
        status: str,
        input_summary: str,
        output_summary: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> ToolCallRecord:
        record = ToolCallRecord(
            tool_name=name,
            status=status,  # type: ignore[arg-type]
            started_at=started_at,
            ended_at=utc_now_iso(),
            elapsed_ms=int((time.perf_counter() - start) * 1000),
            input_summary=input_summary,
            output_summary=output_summary,
            error_code=error_code,
            error_message=error_message,
            role=role,
        )
        self.records.append(record)
        return record
