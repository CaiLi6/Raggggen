"""Context bundle contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContextBundle:
    query: str
    conversation: list[dict[str, str]]
    rag_chunks: list[dict[str, Any]]
    news_items: list[dict[str, Any]]
    market_snapshot: dict[str, Any]
    source_map: dict[str, Any]
    missing_data: list[str]
    conflicts: list[str]
    token_budget: int
    tool_errors: list[str] = field(default_factory=list)
