"""Runtime registry helpers."""

from __future__ import annotations

from typing import Any

from runtime.graph import FinancialResearchRuntime
from tools import create_default_tool_bus


def create_runtime(settings: dict[str, Any] | None = None, mock_tools: bool = False) -> FinancialResearchRuntime:
    bus = create_default_tool_bus(settings=settings, mock_tools=mock_tools)
    return FinancialResearchRuntime(settings=settings, tool_bus=bus)
