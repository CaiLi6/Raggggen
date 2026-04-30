"""Structured research report contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReportSource:
    source_id: str
    title: str
    source_type: str
    url: str | None = None
    snippet: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskDisclosure:
    text: str
    non_investment_advice: str
    limitations: list[str] = field(default_factory=list)


@dataclass
class ResearchReport:
    title: str
    query: str
    thesis: list[str]
    fundamental: str
    sentiment: str
    market_observation: str
    risks: list[str]
    missing_data: list[str]
    next_steps: list[str]
    sources: list[ReportSource]
    disclosure: RiskDisclosure
    trace_id: str | None = None
