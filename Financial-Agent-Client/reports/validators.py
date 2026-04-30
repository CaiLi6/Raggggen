"""Report validation helpers."""

from __future__ import annotations

from reports.schema import ResearchReport
from safety.disclosures import NON_INVESTMENT_ADVICE


def validate_report(report: ResearchReport) -> list[str]:
    errors: list[str] = []
    if not report.query.strip():
        errors.append("report query is empty")
    if not report.thesis:
        errors.append("report thesis is empty")
    if not report.risks:
        errors.append("report risks are empty")
    if not report.sources:
        errors.append("report sources are empty")
    if NON_INVESTMENT_ADVICE not in report.disclosure.non_investment_advice:
        errors.append("non-investment advice disclosure is missing")
    return errors
