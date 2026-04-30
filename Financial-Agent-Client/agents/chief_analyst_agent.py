"""Chief Analyst Agent."""

from __future__ import annotations

from typing import Any

from context.bundle import ContextBundle
from reports.schema import ReportSource, ResearchReport
from safety.disclosures import default_risk_disclosure


class ChiefAnalystAgent:
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        bundle: ContextBundle = state["context_bundle"]
        report = ResearchReport(
            title=self._title(bundle.query),
            query=bundle.query,
            thesis=self._thesis(bundle),
            fundamental=self._fundamental(bundle),
            sentiment=self._sentiment(bundle),
            market_observation=self._market(bundle),
            risks=state.get("risk_findings") or [],
            missing_data=bundle.missing_data,
            next_steps=self._next_steps(bundle),
            sources=self._sources(bundle),
            disclosure=default_risk_disclosure(bundle.missing_data),
            trace_id=state.get("trace_id"),
        )
        state["report"] = report
        return state

    @staticmethod
    def _title(query: str) -> str:
        text = (query or "投研问题").strip()
        return f"{text[:36]} - 本地投研报告"

    @staticmethod
    def _thesis(bundle: ContextBundle) -> list[str]:
        thesis: list[str] = []
        if bundle.rag_chunks:
            thesis.append("内部知识库返回了可引用材料，可作为基本面判断的主要依据。")
        else:
            thesis.append("内部知识库暂未返回足够材料，基本面结论需要谨慎。")
        if bundle.news_items:
            thesis.append("新闻舆情返回了外部事件线索，可用于补充短期催化和情绪观察。")
        else:
            thesis.append("外部新闻工具未提供有效结果，短期情绪判断置信度较低。")
        if bundle.market_snapshot:
            thesis.append("行情模块当前使用摘要观察，真实投资研究仍需接入正式行情 provider。")
        return thesis

    @staticmethod
    def _fundamental(bundle: ContextBundle) -> str:
        if not bundle.rag_chunks:
            return "当前检索工具未返回关于该主题的足够内部知识库材料。"
        lines = []
        for chunk in bundle.rag_chunks[:4]:
            text = str(chunk.get("text") or chunk.get("content") or "").strip()
            source_id = chunk.get("source_id", "S?")
            lines.append(f"- [{source_id}] {text[:360]}")
        return "\n".join(lines)

    @staticmethod
    def _sentiment(bundle: ContextBundle) -> str:
        if not bundle.news_items:
            return "当前新闻舆情工具未返回足够外部事件材料。"
        lines = []
        for item in bundle.news_items[:4]:
            title = str(item.get("title") or "Untitled")
            content = str(item.get("content") or item.get("snippet") or "").strip()
            source_id = item.get("source_id", "S?")
            lines.append(f"- [{source_id}] {title}: {content[:280]}")
        return "\n".join(lines)

    @staticmethod
    def _market(bundle: ContextBundle) -> str:
        if not bundle.market_snapshot:
            return "行情摘要不可用。"
        summary = bundle.market_snapshot.get("summary", "行情摘要未提供。")
        observations = bundle.market_snapshot.get("observations") or []
        if observations:
            return str(summary) + "\n" + "\n".join(f"- {item}" for item in observations)
        return str(summary)

    @staticmethod
    def _next_steps(bundle: ContextBundle) -> list[str]:
        steps = [
            "补充最新财报、公告、电话会纪要和行业数据。",
            "接入真实行情 provider 后复核价格、估值和成交量变化。",
            "对关键结论做来源逐条核验，避免单一来源偏差。",
        ]
        if bundle.missing_data:
            steps.insert(0, "优先补齐数据缺口中列出的缺失信息。")
        return steps

    @staticmethod
    def _sources(bundle: ContextBundle) -> list[ReportSource]:
        sources: list[ReportSource] = []
        for source_id, raw in bundle.source_map.items():
            if not isinstance(raw, dict):
                continue
            sources.append(
                ReportSource(
                    source_id=source_id,
                    title=str(raw.get("title") or source_id),
                    source_type=str(raw.get("source_type") or "unknown"),
                    url=raw.get("url"),
                    snippet=raw.get("snippet"),
                    metadata=dict(raw.get("metadata") or {}),
                )
            )
        return sources
