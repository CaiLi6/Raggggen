"""LLM-as-a-judge evaluation script for faithfulness scoring."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

try:
    from langchain_community.chat_models import ChatDashScope
except ImportError:
    from langchain_community.chat_models.tongyi import ChatTongyi as ChatDashScope


@dataclass
class EvalCase:
    query: str
    historical_context: str
    report: str


def _fallback_faithfulness(context: str, report: str) -> float:
    context_tokens = {tok for tok in context.replace("\n", " ").split(" ") if tok}
    report_tokens = {tok for tok in report.replace("\n", " ").split(" ") if tok}
    if not report_tokens:
        return 0.0
    overlap = len(context_tokens.intersection(report_tokens))
    return round(overlap / max(len(report_tokens), 1), 4)


def judge_faithfulness(case: EvalCase) -> dict[str, Any]:
    prompt = (
        "你是无幻觉性裁判。请只输出 JSON，字段: score(0-1), reason。"
        f"\n[historical_context]\n{case.historical_context}\n"
        f"\n[report]\n{case.report}\n"
    )

    try:
        llm = ChatDashScope(
            model=os.getenv("DASHSCOPE_MODEL", "qwen-plus"),
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
            temperature=0,
        )
        res = llm.invoke(prompt)
        text = str(res.content)
        parsed = json.loads(text)
        return {
            "score": float(parsed.get("score", 0)),
            "reason": str(parsed.get("reason", "")),
            "mode": "llm_judge",
        }
    except Exception:
        return {
            "score": _fallback_faithfulness(case.historical_context, case.report),
            "reason": "Fallback lexical overlap judge used.",
            "mode": "fallback",
        }


def run_eval() -> dict[str, Any]:
    golden_set = [
        EvalCase(
            query="分析特斯拉",
            historical_context="营收增速 18%，毛利率 17%。",
            report="核心观点：营收增速 18%，毛利率 17%，短期情绪偏震荡。",
        ),
        EvalCase(
            query="分析宁德时代",
            historical_context="现金流稳健，研发投入提升。",
            report="核心观点：现金流稳健，研发投入提升，需关注政策波动风险。",
        ),
    ]

    results = [judge_faithfulness(case) for case in golden_set]
    avg_score = round(sum(item["score"] for item in results) / max(len(results), 1), 4)
    return {
        "faithfulness": avg_score,
        "cases": results,
    }


if __name__ == "__main__":
    report = run_eval()
    print(json.dumps(report, ensure_ascii=False, indent=2))
