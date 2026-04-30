"""Compatibility node functions for older LangGraph-style imports."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, BaseMessage

from agents.router_agent import RouterAgent
from gateway.request import GatewayRequest
from observability.trace import ExecutionTrace
from runtime.graph import FinancialResearchRuntime


def _last_user_text(messages: list[BaseMessage]) -> str:
    return str(messages[-1].content) if messages else ""


def router_node(state: dict[str, Any]) -> dict[str, Any]:
    query = _last_user_text(list(state.get("messages", [])))
    route = RouterAgent().route(query)
    return {"research_intent": route.intent, "route_plan": route.route_plan}


async def agent_a_node(state: dict[str, Any]) -> dict[str, Any]:
    result = await _run_compat(state)
    return {
        "historical_context": [result.get("fundamental", "")],
        "errors": result.get("errors", []),
    }


async def agent_b_node(state: dict[str, Any]) -> dict[str, Any]:
    result = await _run_compat(state)
    return {
        "realtime_news": [result.get("sentiment", "")],
        "errors": result.get("errors", []),
    }


def agent_c_node(state: dict[str, Any]) -> dict[str, Any]:
    markdown = str(state.get("markdown") or "")
    if not markdown:
        markdown = "兼容节点未收到完整报告。"
    return {"messages": [AIMessage(content=markdown)]}


async def _run_compat(state: dict[str, Any]) -> dict[str, Any]:
    query = _last_user_text(list(state.get("messages", [])))
    thread_id = str(state.get("thread_id") or "compat-thread")
    request = GatewayRequest(query=query, thread_id=thread_id, metadata={"mock_tools": True})
    trace = ExecutionTrace.start(thread_id=thread_id, query=query)
    runtime = FinancialResearchRuntime()
    result = await runtime.run(request, [{"role": "user", "content": query}], trace)
    return {
        "markdown": result.markdown,
        "fundamental": result.report.fundamental,
        "sentiment": result.report.sentiment,
        "errors": [record.error_code for record in result.tool_records if record.error_code],
    }
