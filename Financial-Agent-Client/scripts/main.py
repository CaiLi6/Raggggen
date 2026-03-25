"""CLI entrypoint for running the financial multi-agent graph with persistence."""

from __future__ import annotations

import argparse
import uuid
from typing import Any
from dotenv import load_dotenv

# 加载根目录下的 .env 文件到系统环境变量中
load_dotenv()

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from core.graph import workflow


def run_once(query: str, thread_id: str) -> dict[str, Any]:
    """Run one graph invocation with SQLite checkpoint persistence."""
    with SqliteSaver.from_conn_string("checkpoints.db") as memory:
        app = workflow.compile(checkpointer=memory)
        config = {"configurable": {"thread_id": thread_id}}
        return app.invoke({"messages": [HumanMessage(content=query)]}, config=config)


def main(thread_id: str | None = None, query: str | None = None) -> None:
    active_thread = thread_id or f"thread-{uuid.uuid4().hex[:8]}"

    if query:
        result = run_once(query=query, thread_id=active_thread)
        messages = result.get("messages", [])
        if messages:
            print(messages[-1].content)
        return

    print(f"[session] thread_id={active_thread}")
    print("输入问题开始分析，输入 exit 退出。")
    while True:
        user_input = input("Query> ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        result = run_once(query=user_input, thread_id=active_thread)
        messages = result.get("messages", [])
        print("\n--- Report ---")
        if messages:
            print(messages[-1].content)
        print("--------------\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Financial LangGraph CLI")
    parser.add_argument("--thread-id", default=None, help="Stable thread id for checkpoint resume")
    parser.add_argument("--query", default=None, help="Run one-shot query and exit")
    args = parser.parse_args()
    main(thread_id=args.thread_id, query=args.query)
