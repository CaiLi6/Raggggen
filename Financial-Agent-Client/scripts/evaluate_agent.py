"""Batch evaluator for CI/CD using the core AgentEvaluator module."""

from __future__ import annotations

import asyncio
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.evaluator import AgentEvaluator
from core.graph import workflow


def _last_report(state: dict[str, Any]) -> str:
    messages = list(state.get("messages", []))
    if not messages:
        return ""
    return str(messages[-1].content)


def _normalize_queries(data: Any) -> list[str]:
    if isinstance(data, list):
        queries: list[str] = []
        for item in data:
            if isinstance(item, str) and item.strip():
                queries.append(item.strip())
            elif isinstance(item, dict):
                raw = str(item.get("query", "")).strip()
                if raw:
                    queries.append(raw)
        return queries
    return []


def load_queries(cases_file: str | None) -> list[str]:
    if not cases_file:
        return [
            "请结合财报和舆情分析合合信息的投资价值",
            "请分析特斯拉近期基本面与舆情变化",
            "请评估宁德时代短中期投资风险与机会",
        ]

    path = Path(cases_file)
    content = json.loads(path.read_text(encoding="utf-8"))
    queries = _normalize_queries(content)
    if not queries:
        raise ValueError("测试集为空，JSON 应为字符串列表或包含 query 字段的对象列表。")
    return queries


async def run_batch_eval(queries: list[str]) -> dict[str, Any]:
    app = workflow.compile()
    evaluator = AgentEvaluator()
    results: list[dict[str, Any]] = []

    total_start = time.perf_counter()
    for idx, query in enumerate(queries, start=1):
        start = time.perf_counter()
        state = await app.ainvoke(
            {"messages": [HumanMessage(content=query)]},
            config={"configurable": {"thread_id": f"eval-{idx}"}},
        )
        latency_seconds = time.perf_counter() - start

        historical_context = "\n\n".join([str(x) for x in state.get("historical_context", [])])
        realtime_news = "\n\n".join([str(x) for x in state.get("realtime_news", [])])
        report_text = _last_report(state)

        score = evaluator.evaluate(
            query=query,
            historical_context=historical_context,
            realtime_news=realtime_news,
            final_report=report_text,
        )

        results.append(
            {
                "query": query,
                "latency_seconds": latency_seconds,
                "faithfulness": score.faithfulness.score,
                "faithfulness_reasoning": score.faithfulness.reasoning,
                "answer_relevance": score.answer_relevance.score,
                "answer_relevance_reasoning": score.answer_relevance.reasoning,
            }
        )

    total_latency = time.perf_counter() - total_start
    avg_faithfulness = sum(item["faithfulness"] for item in results) / max(len(results), 1)
    avg_relevance = sum(item["answer_relevance"] for item in results) / max(len(results), 1)
    avg_latency = sum(item["latency_seconds"] for item in results) / max(len(results), 1)

    return {
        "count": len(results),
        "avg_faithfulness": avg_faithfulness,
        "avg_answer_relevance": avg_relevance,
        "avg_latency_seconds": avg_latency,
        "total_latency_seconds": total_latency,
        "results": results,
    }


def _print_batch_report(summary: dict[str, Any]) -> None:
    print("=" * 72)
    print("Financial Agent Batch Evaluation Report")
    print("=" * 72)
    print(f"Cases: {summary['count']}")
    print(f"Total Latency: {summary['total_latency_seconds']:.2f}s")
    print(f"Average Latency: {summary['avg_latency_seconds']:.2f}s")
    print(f"Average Faithfulness: {summary['avg_faithfulness']:.2f}/10")
    print(f"Average Answer Relevance: {summary['avg_answer_relevance']:.2f}/10")
    print("-" * 72)
    for idx, item in enumerate(summary["results"], start=1):
        print(f"[{idx}] Query: {item['query']}")
        print(f"    Latency: {item['latency_seconds']:.2f}s")
        print(f"    Faithfulness: {item['faithfulness']}/10")
        print(f"    Reasoning: {item['faithfulness_reasoning']}")
        print(f"    Answer Relevance: {item['answer_relevance']}/10")
        print(f"    Reasoning: {item['answer_relevance_reasoning']}")
        print("-" * 72)
    print("=" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch evaluate financial agent quality")
    parser.add_argument(
        "--cases-file",
        default=None,
        help="JSON file path. Supports ['q1','q2'] or [{'query':'...'}]",
    )
    args = parser.parse_args()

    load_dotenv()
    queries = load_queries(args.cases_file)
    summary = asyncio.run(run_batch_eval(queries))
    _print_batch_report(summary)


if __name__ == "__main__":
    main()
