"""Tool permission policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DEFAULT_ALLOWED_TOOLS = {"rag_search", "news_search", "market_data", "evaluate_report"}
DEFAULT_DENIED_TOOLS = {
    "broker_order",
    "broker_cancel_order",
    "bank_transfer",
    "payment",
    "credential_reader",
}


@dataclass
class ToolPolicy:
    allowed_tools: set[str] = field(default_factory=lambda: set(DEFAULT_ALLOWED_TOOLS))
    denied_tools: set[str] = field(default_factory=lambda: set(DEFAULT_DENIED_TOOLS))
    prohibited_actions: set[str] = field(default_factory=set)
    confirm_required: set[str] = field(default_factory=set)

    @classmethod
    def from_raw(cls, raw: dict[str, Any] | None = None) -> "ToolPolicy":
        raw = raw or {}
        allowed = set(raw.get("allowed_tools") or DEFAULT_ALLOWED_TOOLS)
        denied = set(raw.get("denied_tools") or DEFAULT_DENIED_TOOLS)
        return cls(
            allowed_tools=allowed,
            denied_tools=denied,
            prohibited_actions=set(raw.get("prohibited_actions") or []),
            confirm_required=set(raw.get("confirm_required") or []),
        )

    def is_allowed(self, tool_name: str) -> bool:
        if tool_name in self.denied_tools:
            return False
        if self.allowed_tools and tool_name not in self.allowed_tools:
            return False
        return True

    def require_allowed(self, tool_name: str) -> None:
        if not self.is_allowed(tool_name):
            raise PermissionError(f"Tool '{tool_name}' is denied by policy")
