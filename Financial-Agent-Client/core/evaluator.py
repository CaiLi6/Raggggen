"""Core LLM-as-a-judge evaluator for agent output quality."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

try:
    from langchain_community.chat_models import ChatDashScope
except ImportError:
    from langchain_community.chat_models.tongyi import ChatTongyi as ChatDashScope


@dataclass
class MetricScore:
    metric: str
    score: int
    reasoning: str


@dataclass
class EvaluationResult:
    faithfulness: MetricScore
    answer_relevance: MetricScore


class AgentEvaluator:
    """Evaluate report quality with a DashScope LLM judge."""

    def __init__(self) -> None:
        self.llm = ChatDashScope(
            model=os.getenv("DASHSCOPE_MODEL", "qwen-plus"),
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
            temperature=0,
        )

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        payload = text.strip()
        if payload.startswith("```"):
            payload = re.sub(r"^```(?:json)?", "", payload).strip()
            payload = re.sub(r"```$", "", payload).strip()
        try:
            result = json.loads(payload)
            return result if isinstance(result, dict) else {}
        except Exception:
            pass

        match = re.search(r"\{[\s\S]*\}", payload)
        if not match:
            return {}
        try:
            result = json.loads(match.group(0))
            return result if isinstance(result, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _clamp_score(value: Any) -> int:
        try:
            score = int(round(float(value)))
        except Exception:
            score = 1
        return max(1, min(10, score))

    def _judge_metric(
        self,
        metric_name: str,
        rubric: str,
        query: str,
        historical_context: str,
        realtime_news: str,
        final_report: str,
    ) -> MetricScore:
        prompt = (
            "你是严格的金融投研报告评审员。请只输出 JSON，且不得输出额外文字。"
            "JSON 格式必须是: "
            '{"score": <1-10整数>, "reasoning": "<不超过80字的简短理由>"}。\n\n'
            f"[Metric]\n{metric_name}\n\n"
            f"[Rubric]\n{rubric}\n\n"
            f"[User Query]\n{query}\n\n"
            f"[Historical Context]\n{historical_context}\n\n"
            f"[Realtime News]\n{realtime_news}\n\n"
            f"[Final Report]\n{final_report}\n"
        )

        try:
            response = self.llm.invoke(prompt)
            raw = str(response.content)
            parsed = self._extract_json(raw)
            score = self._clamp_score(parsed.get("score", 1))
            reasoning = str(parsed.get("reasoning", "裁判未提供理由")).strip() or "裁判未提供理由"
            return MetricScore(metric=metric_name, score=score, reasoning=reasoning)
        except Exception as exc:
            return MetricScore(metric=metric_name, score=1, reasoning=f"裁判调用失败: {exc}")

    def evaluate(
        self,
        query: str,
        historical_context: str,
        realtime_news: str,
        final_report: str,
    ) -> EvaluationResult:
        faithfulness = self._judge_metric(
            metric_name="Faithfulness",
            rubric=(
                "判断最终报告是否严格基于 Historical Context 和 Realtime News。"
                "若有编造数据、无法回溯来源或越界推断应低分。"
                "10分表示几乎无幻觉且结论可被证据支撑。"
            ),
            query=query,
            historical_context=historical_context,
            realtime_news=realtime_news,
            final_report=final_report,
        )

        relevance = self._judge_metric(
            metric_name="Answer Relevance",
            rubric=(
                "判断最终报告是否直接、完整回答用户问题，"
                "并覆盖问题关键维度，避免无关泛化叙述。"
                "10分表示回答精准且与问题高度一致。"
            ),
            query=query,
            historical_context=historical_context,
            realtime_news=realtime_news,
            final_report=final_report,
        )

        return EvaluationResult(
            faithfulness=faithfulness,
            answer_relevance=relevance,
        )
