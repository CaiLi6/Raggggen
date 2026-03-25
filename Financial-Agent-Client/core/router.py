"""Intent router for investment research requests."""

from __future__ import annotations

import os

try:
    from langchain_community.chat_models import ChatDashScope
except ImportError:
    from langchain_community.chat_models.tongyi import ChatTongyi as ChatDashScope


_ALLOWED_INTENTS = {"fundamental", "sentiment", "comprehensive", "unknown"}


def intent_router(query: str) -> str:
    """Classify user query into one of four research intents via DashScope LLM."""
    text = (query or "").strip()
    if not text:
        return "unknown"

    llm = ChatDashScope(
        model=os.getenv("DASHSCOPE_ROUTER_MODEL", "qwen-turbo"),
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
        temperature=0,
    )
    response = llm.invoke(
        [
            (
                "system",
                "你是意图分类器。只输出一个标签：fundamental、sentiment、comprehensive、unknown。",
            ),
            ("human", f"问题：{text}"),
        ]
    )
    intent = str(response.content).strip().lower()
    return intent if intent in _ALLOWED_INTENTS else "unknown"
