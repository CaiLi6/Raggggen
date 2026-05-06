"""Tests for agents/router_agent.py (task F3)."""

from __future__ import annotations

from agents.router_agent import RouterAgent, RouteDecision


def test_route_returns_route_decision() -> None:
    agent = RouterAgent()
    decision = agent.route("分析苹果公司的财报")
    assert isinstance(decision, RouteDecision)


def test_fundamental_keywords_trigger_fundamental() -> None:
    agent = RouterAgent()
    decision = agent.route("苹果公司的财报分析")
    assert "fundamental" in decision.route_plan


def test_sentiment_keywords_trigger_sentiment() -> None:
    agent = RouterAgent()
    decision = agent.route("最新新闻舆情如何")
    assert "sentiment" in decision.route_plan


def test_market_keywords_trigger_market() -> None:
    agent = RouterAgent()
    decision = agent.route("今天行情怎么样")
    assert "market_data" in decision.route_plan


def test_route_plan_always_includes_risk_and_compliance() -> None:
    agent = RouterAgent()
    for query in ["分析财报", "新闻舆情", "行情价格", "随机问题"]:
        decision = agent.route(query)
        assert "risk" in decision.route_plan
        assert "chief_analyst" in decision.route_plan
        assert "compliance" in decision.route_plan


def test_unrecognized_query_routes_all_agents() -> None:
    agent = RouterAgent()
    decision = agent.route("这是一个随机问题")
    assert "fundamental" in decision.route_plan
    assert "sentiment" in decision.route_plan
    assert "market_data" in decision.route_plan


def test_fundamental_intent_when_only_fundamental() -> None:
    agent = RouterAgent()
    decision = agent.route("财报分析")
    assert decision.intent in ("fundamental", "comprehensive")


def test_comprehensive_intent_when_both() -> None:
    agent = RouterAgent()
    decision = agent.route("财报和新闻舆情综合分析")
    assert decision.intent == "comprehensive"


def test_empty_query_routes_all() -> None:
    agent = RouterAgent()
    decision = agent.route("")
    assert len(decision.route_plan) >= 5


def test_route_plan_order_ends_with_compliance() -> None:
    agent = RouterAgent()
    decision = agent.route("任意问题")
    assert decision.route_plan[-1] == "compliance"
