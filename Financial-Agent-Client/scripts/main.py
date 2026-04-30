"""CLI entry point for FinAgent OS Client."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Sequence

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
from gateway.response import GatewayResponse


def run_once(
    query: str,
    thread_id: str | None = None,
    collection: str | None = None,
    output_format: str = "markdown",
    mock_tools: bool = False,
    enable_eval: bool = False,
) -> GatewayResponse:
    gateway = AppGateway()
    request = GatewayRequest.from_cli(
        query=query,
        thread_id=thread_id or f"cli-{uuid.uuid4().hex[:8]}",
        collection=collection,
        enable_eval=enable_eval,
        output_format=output_format,
        mock_tools=mock_tools,
    )
    return gateway.handle(request)


def _print_response(response: GatewayResponse, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(response.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(response.markdown)
        if response.errors:
            print("\nErrors:")
            for error in response.errors:
                print(f"- {error}")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="FinAgent OS Client CLI")
    parser.add_argument("--thread-id", default=None, help="Stable thread id for session history")
    parser.add_argument("--query", default=None, help="Run one-shot query and exit")
    parser.add_argument("--collection", default=None, help="RAG collection name")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    parser.add_argument("--mock-tools", action="store_true", help="Use deterministic mock research tools")
    parser.add_argument("--enable-eval", action="store_true", help="Run lightweight evaluation")
    args = parser.parse_args(argv)

    load_dotenv()
    active_thread = args.thread_id or f"cli-{uuid.uuid4().hex[:8]}"

    if args.query:
        response = run_once(
            query=args.query,
            thread_id=active_thread,
            collection=args.collection,
            output_format=args.format,
            mock_tools=args.mock_tools,
            enable_eval=args.enable_eval,
        )
        _print_response(response, args.format)
        return

    print(f"[session] thread_id={active_thread}")
    print("Input a research question, or type exit to quit.")
    while True:
        user_input = input("Query> ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        response = run_once(
            query=user_input,
            thread_id=active_thread,
            collection=args.collection,
            output_format=args.format,
            mock_tools=args.mock_tools,
            enable_eval=args.enable_eval,
        )
        _print_response(response, args.format)
        print()


if __name__ == "__main__":
    main()
