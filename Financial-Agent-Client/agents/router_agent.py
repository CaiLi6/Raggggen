"""Router Agent."""

from __future__ import annotations

from dataclasses import dataclass


FUNDAMENTAL_KEYWORDS = ["财报", "基本面", "估值", "营收", "利润", "现金流", "研报", "公告", "fundamental"]
SENTIMENT_KEYWORDS = ["新闻", "舆情", "情绪", "事件", "催化", "sentiment", "news"]
MARKET_KEYWORDS = ["行情", "股价", "价格", "成交", "量价", "估值分位", "market"]


@dataclass
class RouteDecision:
    intent: str
    route_plan: list[str]


class RouterAgent:
    def route(self, query: str) -> RouteDecision:
        text = (query or "").lower()
        wants_fundamental = any(keyword.lower() in text for keyword in FUNDAMENTAL_KEYWORDS)
        wants_sentiment = any(keyword.lower() in text for keyword in SENTIMENT_KEYWORDS)
        wants_market = any(keyword.lower() in text for keyword in MARKET_KEYWORDS)

        if not any([wants_fundamental, wants_sentiment, wants_market]):
            wants_fundamental = True
            wants_sentiment = True
            wants_market = True

        plan: list[str] = []
        if wants_fundamental:
            plan.append("fundamental")
        if wants_sentiment:
            plan.append("sentiment")
        if "market_data" not in plan:
            plan.append("market_data")
        plan.extend(["risk", "chief_analyst", "compliance"])

        if wants_fundamental and wants_sentiment:
            intent = "comprehensive"
        elif wants_fundamental:
            intent = "fundamental"
        elif wants_sentiment:
            intent = "sentiment"
        elif wants_market:
            intent = "market"
        else:
            intent = "unknown"
        return RouteDecision(intent=intent, route_plan=plan)
