"""Tests for tools/evaluator_tool.py (task G4)."""

from __future__ import annotations

from tools.evaluator_tool import EvaluatorTool, EvaluationMetric


def _make_good_markdown(query: str) -> str:
    return f"""# Report
{query}
## 主要风险
- 市场风险
## 非投资建议声明
本报告不构成投资建议。
"""


def test_evaluator_returns_dict_with_metrics() -> None:
    tool = EvaluatorTool()
    result = tool("AAPL分析", _make_good_markdown("AAPL分析"))
    assert "metrics" in result
    assert "overall" in result


def test_evaluator_metrics_are_list_of_dicts() -> None:
    tool = EvaluatorTool()
    result = tool("query", _make_good_markdown("query"))
    for m in result["metrics"]:
        assert "name" in m
        assert "score" in m
        assert "reason" in m


def test_evaluator_overall_is_float() -> None:
    tool = EvaluatorTool()
    result = tool("q", _make_good_markdown("q"))
    assert isinstance(result["overall"], float)


def test_evaluator_answer_relevance_high_when_query_in_report() -> None:
    tool = EvaluatorTool()
    query = "苹果公司财务分析"
    markdown = f"# Report\n{query}\n风险\n不构成投资建议"
    result = tool(query, markdown)
    ar = next(m for m in result["metrics"] if m["name"] == "answer_relevance")
    assert ar["score"] == 1.0


def test_evaluator_answer_relevance_lower_when_query_missing() -> None:
    tool = EvaluatorTool()
    result = tool("missing query xyz", "# Report\n风险\n不构成投资建议")
    ar = next(m for m in result["metrics"] if m["name"] == "answer_relevance")
    assert ar["score"] < 1.0


def test_evaluator_source_coverage_with_sources() -> None:
    tool = EvaluatorTool()
    sources = [{"source_id": "S1"}, {"source_id": "S2"}]
    result = tool("q", "# Report", sources=sources)
    sc = next(m for m in result["metrics"] if m["name"] == "source_coverage")
    assert sc["score"] == 1.0


def test_evaluator_source_coverage_no_sources() -> None:
    tool = EvaluatorTool()
    result = tool("q", "# Report", sources=[])
    sc = next(m for m in result["metrics"] if m["name"] == "source_coverage")
    assert sc["score"] == 0.0


def test_evaluator_risk_disclosure_full_score() -> None:
    tool = EvaluatorTool()
    markdown = "# Report\n风险提示\n不构成投资建议"
    result = tool("q", markdown)
    rd = next(m for m in result["metrics"] if m["name"] == "risk_disclosure")
    assert rd["score"] == 1.0


def test_evaluator_risk_disclosure_zero_when_missing() -> None:
    tool = EvaluatorTool()
    result = tool("q", "# Report\n没有风险没有声明")
    rd = next(m for m in result["metrics"] if m["name"] == "risk_disclosure")
    assert rd["score"] == 0.0


def test_evaluator_overall_is_average() -> None:
    tool = EvaluatorTool()
    result = tool("q", "# Report")
    scores = [m["score"] for m in result["metrics"]]
    expected = round(sum(scores) / len(scores), 4)
    assert result["overall"] == expected
