from __future__ import annotations

from reports.renderer import ReportRenderer
from reports.schema import ReportSource, ResearchReport
from safety.disclosures import default_risk_disclosure


def test_renderer_includes_required_sections() -> None:
    report = ResearchReport(
        title="投研报告",
        query="分析 TSLA",
        thesis=["核心观点"],
        fundamental="基本面",
        sentiment="情绪",
        market_observation="行情",
        risks=["风险"],
        missing_data=["缺口"],
        next_steps=["下一步"],
        sources=[ReportSource(source_id="S1", title="source", source_type="mock")],
        disclosure=default_risk_disclosure(),
        trace_id="trace-test",
    )
    markdown = ReportRenderer().render_markdown(report)
    assert "## 用户问题" in markdown
    assert "## 信息来源" in markdown
    assert "不构成投资建议" in markdown
