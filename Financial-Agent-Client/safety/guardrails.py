"""Safety guardrails for research-only financial output."""

from __future__ import annotations

from dataclasses import dataclass, field

from reports.schema import ResearchReport
from safety.disclosures import NON_INVESTMENT_ADVICE
from safety.policy import PROHIBITED_QUERY_PATTERNS, PROHIBITED_REPORT_PATTERNS


@dataclass
class SafetyCheckResult:
    ok: bool
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class SafetyGuardrails:
    """Research-only policy checks."""

    def validate_query(self, query: str) -> SafetyCheckResult:
        text = query or ""
        violations = [
            f"prohibited query pattern: {pattern}"
            for pattern in PROHIBITED_QUERY_PATTERNS
            if pattern in text
        ]
        return SafetyCheckResult(ok=not violations, violations=violations)

    def validate_report(self, report: ResearchReport) -> SafetyCheckResult:
        report_text = "\n".join(
            [
                report.title,
                report.query,
                " ".join(report.thesis),
                report.fundamental,
                report.sentiment,
                report.market_observation,
                " ".join(report.risks),
                report.disclosure.text,
                report.disclosure.non_investment_advice,
            ]
        )
        violations = [
            f"prohibited report pattern: {pattern}"
            for pattern in PROHIBITED_REPORT_PATTERNS
            if pattern in report_text
        ]
        warnings: list[str] = []
        if not report.sources:
            warnings.append("report has no sources")
        if not report.risks:
            warnings.append("report has no risks")
        if NON_INVESTMENT_ADVICE not in report.disclosure.non_investment_advice:
            warnings.append("non-investment advice disclosure is missing or changed")
        return SafetyCheckResult(ok=not violations, violations=violations, warnings=warnings)
