"""StateGraph topology for the multi-agent research workflow."""

from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from agents.nodes import agent_a_node, agent_b_node, agent_c_node
from core.router import intent_router
from core.state import AgentState


def router_node(state: AgentState) -> dict[str, str]:
    messages = list(state.get("messages", []))
    query = str(messages[-1].content) if messages else ""
    return {"research_intent": intent_router(query)}


workflow = StateGraph(AgentState)

workflow.add_node("router", router_node)
workflow.add_node("agent_a", agent_a_node)
workflow.add_node("agent_b", agent_b_node)
workflow.add_node("agent_c", agent_c_node)

workflow.add_edge(START, "router")


def _route_edges(state: dict[str, Any]) -> list[Literal["agent_a", "agent_b"]]:
    intent = state.get("research_intent", "unknown")
    if intent == "fundamental":
        return ["agent_a"]
    if intent == "sentiment":
        return ["agent_b"]
    if intent == "comprehensive":
        return ["agent_a", "agent_b"]
    return ["agent_a", "agent_b"]


workflow.add_conditional_edges("router", _route_edges, ["agent_a", "agent_b"])
workflow.add_edge("agent_a", "agent_c")
workflow.add_edge("agent_b", "agent_c")
workflow.add_edge("agent_c", END)
