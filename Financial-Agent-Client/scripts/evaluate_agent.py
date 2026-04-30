"""Batch evaluator for FinAgent OS Client."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv() -> None:
        return None

from gateway.app_gateway import AppGateway
from gateway.request import GatewayRequest


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
            "请结合财报和舆情分析特斯拉近期投资价值",
            "请评估宁德时代短中期投资风险与机会",
            "分析 AAPL 的基本面和短期情绪",
        ]
    path = Path(cases_file)
    queries = _normalize_queries(json.loads(path.read_text(encoding="utf-8")))
    if not queries:
        raise ValueError("cases file must contain strings or objects with a query field")
    return queries


def run_batch_eval(queries: list[str], mock_tools: bool = True) -> dict[str, Any]:
    gateway = AppGateway()
    results: list[dict[str, Any]] = []
    start_all = time.perf_counter()
    for index, query in enumerate(queries, start=1):
        start = time.perf_counter()
        response = gateway.handle(
            GatewayRequest.from_cli(
                query=query,
                thread_id=f"eval-{index}",
                enable_eval=True,
                mock_tools=mock_tools,
            )
        )
        results.append(
            {
                "query": query,
                "trace_id": response.trace_id,
                "latency_seconds": round(time.perf_counter() - start, 4),
                "errors": response.errors,
                "warnings": response.warnings,
                "evaluation": response.metadata.get("evaluation"),
            }
        )
    return {
        "count": len(results),
        "total_latency_seconds": round(time.perf_counter() - start_all, 4),
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch evaluate FinAgent OS Client")
    parser.add_argument("--cases-file", default=None)
    parser.add_argument("--real-tools", action="store_true", help="Use real adapters instead of mocks")
    args = parser.parse_args()

    load_dotenv()
    summary = run_batch_eval(load_queries(args.cases_file), mock_tools=not args.real_tools)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
