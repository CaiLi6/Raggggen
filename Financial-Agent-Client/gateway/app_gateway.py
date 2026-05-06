"""Application Gateway for UI, CLI and tests."""

from __future__ import annotations

import asyncio
from typing import Any

from config.loader import ConfigLoader
from gateway.request import GatewayRequest
from gateway.response import GatewayResponse
from gateway.session import SessionManager
from observability.audit import JsonlTraceWriter
from observability.trace import ExecutionTrace
from runtime.registry import create_runtime


class AppGateway:
    """Unified application entry point."""

    def __init__(
        self,
        config_loader: ConfigLoader | None = None,
        session_manager: SessionManager | None = None,
    ):
        self.config_loader = config_loader or ConfigLoader()
        if session_manager is None:
            settings = self.config_loader.load_settings()
            db_path = settings.get("session", {}).get("db_path")
            session_manager = SessionManager(db_path=db_path)
        self.session_manager = session_manager

    def handle(self, request: GatewayRequest) -> GatewayResponse:
        return asyncio.run(self.ahandle(request))

    async def ahandle(self, request: GatewayRequest) -> GatewayResponse:
        thread_id = request.thread_id or self.session_manager.new_thread_id()
        trace = ExecutionTrace.start(thread_id=thread_id, query=request.query)
        settings = self.config_loader.load_settings()
        try:
            request.validate()
            session = self.session_manager.get_or_create(thread_id)
            self.session_manager.append(thread_id, "user", request.normalized_query)
            mock_tools = bool(request.metadata.get("mock_tools", False))
            runtime = create_runtime(settings=settings, mock_tools=mock_tools)
            result = await runtime.run(request, conversation=session.history, trace=trace)
            self.session_manager.append(thread_id, "assistant", result.markdown)
            trace.warnings.extend(result.warnings)
            trace.errors.extend(result.errors)
            trace.finish()
            self._write_trace(settings, trace.to_dict())
            return GatewayResponse.ok(
                trace_id=trace.trace_id,
                thread_id=thread_id,
                markdown=result.markdown,
                report=result.report,
                tool_records=result.tool_records,
                warnings=result.warnings,
                errors=result.errors,
                metadata=result.metadata,
            )
        except Exception as exc:
            trace.add_error(str(exc))
            trace.finish()
            self._write_trace(settings, trace.to_dict())
            return GatewayResponse.error(trace_id=trace.trace_id, thread_id=thread_id, message=str(exc))

    @staticmethod
    def _write_trace(settings: dict[str, Any], payload: dict[str, Any]) -> None:
        observability = settings.get("observability", {})
        if not observability.get("write_jsonl", True):
            return
        writer = JsonlTraceWriter(
            trace_dir=observability.get("trace_dir", "logs"),
            file_name=observability.get("client_trace_file", "client_traces.jsonl"),
        )
        writer.write(payload)
