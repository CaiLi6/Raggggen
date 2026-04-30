"""Compliance Reviewer Agent."""

from __future__ import annotations

from typing import Any

from reports.schema import ResearchReport
from safety.guardrails import SafetyGuardrails


class ComplianceReviewerAgent:
    def __init__(self, guardrails: SafetyGuardrails | None = None):
        self.guardrails = guardrails or SafetyGuardrails()

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        report: ResearchReport = state["report"]
        result = self.guardrails.validate_report(report)
        state.setdefault("warnings", []).extend(result.warnings)
        state.setdefault("errors", []).extend(result.violations)
        state["safety_result"] = {
            "ok": result.ok,
            "warnings": result.warnings,
            "violations": result.violations,
        }
        return state
