"""Render structured reports for CLI and Streamlit."""

from __future__ import annotations

import json
from dataclasses import asdict

from reports.schema import ResearchReport


def _bullet(items: list[str], fallback: str) -> str:
    values = [item for item in items if item]
    if not values:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in values)


class ReportRenderer:
    def render_markdown(self, report: ResearchReport) -> str:
        sources = []
        for source in report.sources:
            line = f"- [{source.source_id}] {source.source_type}: {source.title}"
            if source.url:
                line += f" ({source.url})"
            if source.snippet:
                line += f" - {source.snippet}"
            sources.append(line)
        source_text = "\n".join(sources) if sources else "- 暂无可用来源，已在数据缺口中标注。"

        limitations = _bullet(report.disclosure.limitations, "未发现额外限制。")

        return "\n\n".join(
            [
                f"# {report.title}",
                f"trace_id: `{report.trace_id or 'n/a'}`",
                f"## 用户问题\n{report.query}",
                f"## 核心观点\n{_bullet(report.thesis, '当前证据不足，暂不形成明确观点。')}",
                f"## 基本面支撑\n{report.fundamental}",
                f"## 短期情绪与事件\n{report.sentiment}",
                f"## 行情与估值观察\n{report.market_observation}",
                f"## 主要风险\n{_bullet(report.risks, '需关注数据不足导致的判断偏差。')}",
                f"## 数据缺口与不确定性\n{_bullet(report.missing_data, '暂无显著数据缺口。')}",
                f"## 后续研究清单\n{_bullet(report.next_steps, '补充更多一手资料后再复核结论。')}",
                f"## 信息来源\n{source_text}",
                f"## 风险披露\n{report.disclosure.text}\n\n{limitations}",
                f"## 非投资建议声明\n{report.disclosure.non_investment_advice}",
            ]
        )

    def render_json(self, report: ResearchReport) -> str:
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
