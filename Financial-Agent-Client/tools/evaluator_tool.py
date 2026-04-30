"""Lightweight report evaluator used by CLI and tests."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class EvaluationMetric:
    name: str
    score: float
    reason: str


class EvaluatorTool:
    """Deterministic fallback evaluator for local regression."""

    def __call__(self, query: str, report_markdown: str, sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        sources = sources or []
        has_disclosure = "不构成投资建议" in report_markdown
        has_risk = "风险" in report_markdown
        has_query = query.strip() in report_markdown
        source_score = min(1.0, len(sources) / 2) if sources else 0.0
        metrics = [
            EvaluationMetric("answer_relevance", 1.0 if has_query else 0.5, "checks whether query is reflected"),
            EvaluationMetric("source_coverage", source_score, "checks whether sources are present"),
            EvaluationMetric("risk_disclosure", 1.0 if has_risk and has_disclosure else 0.0, "checks risk and disclosure"),
        ]
        return {
            "metrics": [asdict(metric) for metric in metrics],
            "overall": round(sum(metric.score for metric in metrics) / len(metrics), 4),
        }
