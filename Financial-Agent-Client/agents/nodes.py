"""Agent node implementations for the LangGraph workflow."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

try:
    from langchain_community.chat_models import ChatDashScope
except ImportError:
    from langchain_community.chat_models.tongyi import ChatTongyi as ChatDashScope
from langchain_core.messages import AIMessage, BaseMessage

from core.router import intent_router
from core.state import AgentState
from infrastructure.tools import get_rag_context, web_search_sentiment


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def _last_user_text(messages: list[BaseMessage]) -> str:
    if not messages:
        return ""
    return str(messages[-1].content)


def router_node(state: AgentState) -> dict[str, Any]:
    messages = list(state.get("messages", []))
    query = _last_user_text(messages)
    logger.info("👉 [Router] Entry | query=%s", query)
    intent = intent_router(query)
    logger.info("✅ [Router] Exit | intent=%s", intent)
    return {"research_intent": intent}


async def agent_a_node(state: AgentState) -> dict[str, Any]:
    logger.info("👉 [Agent A] Entry | start MCP private knowledge query")
    messages = list(state.get("messages", []))
    query = _last_user_text(messages)
    errors: list[str] = []
    historical_context: list[str] = []

    try:
        logger.info("👉 [Agent A] 正在调用 MCP 获取私有数据 | query=%s", query)
        result = await get_rag_context(query=query, top_k=1)
        if result.startswith("MCP_SERVER_UNAVAILABLE"):
            errors.append("MCP_SERVER_UNAVAILABLE")
            logger.error("❌ [Agent A] MCP unavailable | detail=%s", result)
        elif result.startswith("MCP_CONNECTED_BUT_QUERY_TIMEOUT"):
            errors.append("MCP_SERVER_UNAVAILABLE")
            logger.error("❌ [Agent A] MCP timeout | detail=%s", result)
        elif result.startswith("MCP_CONNECTED_BUT_TOOL_ERROR"):
            errors.append("MCP_SERVER_UNAVAILABLE")
            logger.error("❌ [Agent A] MCP tool error | detail=%s", result)
        else:
            historical_context.append(result)
            logger.info("✅ [Agent A] 获取成功，内容长度: %s", len(result))
    except Exception:
        logger.exception("❌ [Agent A] Unexpected failure while fetching MCP data")
        errors.append("MCP_SERVER_UNAVAILABLE")

    logger.info(
        "✅ [Agent A] Exit | historical_count=%s errors=%s",
        len(historical_context),
        errors,
    )
    return {
        "historical_context": historical_context,
        "errors": errors,
    }


async def agent_b_node(state: AgentState) -> dict[str, Any]:
    logger.info("👉 [Agent B] Entry | start realtime sentiment search")
    messages = list(state.get("messages", []))
    query = _last_user_text(messages).strip()
    errors: list[str] = []
    realtime_news: list[str] = []

    if not query:
        logger.error("❌ [Agent B] Empty query; skip search")
        return {
            "realtime_news": realtime_news,
            "errors": ["WEB_SEARCH_FAILED"],
        }

    try:
        logger.info("👉 [Agent B] 正在调用 Tavily | query=%s", query)
        data = await web_search_sentiment(query)
        if data.get("error") == "WEB_SEARCH_FAILED":
            errors.append("WEB_SEARCH_FAILED")
            logger.error("❌ [Agent B] Tavily failed | detail=%s", data)
        else:
            realtime_news.append(json.dumps(data, ensure_ascii=False))
            logger.info(
                "✅ [Agent B] 获取成功，结果条数: %s",
                len(data.get("results", [])) if isinstance(data.get("results"), list) else 1,
            )
    except Exception:
        logger.exception("❌ [Agent B] Unexpected failure while searching Tavily")
        errors.append("WEB_SEARCH_FAILED")

    logger.info(
        "✅ [Agent B] Exit | realtime_count=%s errors=%s",
        len(realtime_news),
        errors,
    )
    return {
        "realtime_news": realtime_news,
        "errors": errors,
    }


def agent_c_node(state: AgentState) -> dict[str, Any]:
    logger.info("👉 [Agent C] Entry | start synthesis")
    messages = list(state.get("messages", []))
    user_query = _last_user_text(messages).strip()
    errors = list(state.get("errors", []))
    historical_context = list(state.get("historical_context", []))
    realtime_news = list(state.get("realtime_news", []))

    llm = ChatDashScope(
        model=os.getenv("DASHSCOPE_MODEL", "qwen-plus"),
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
        temperature=0.2,
    )
    reply = llm.invoke(
        [
            (
                "system",
                "你是一个严谨的金融分析师。你必须仅仅依赖提供的 [Historical Context] 和 "
                "[Realtime News] 来回答用户的问题。"
                "如果提供的信息中没有关于用户问题（如特定行业/股票）的具体数据，你必须诚实地指出"
                "'当前检索工具未返回关于该主题的足够信息'，绝对禁止使用通用宏观大盘套话"
                "（如全A盈利、美联储降息等）来凑字数敷衍。"
                "输出必须为 Markdown，且不得使用代码块包裹。"
                "必须在结论中显式引用来源，并单独提供“信息来源”小节。"
                "信息来源必须严格按两类分组输出："
                "1) 内部知识库（Agent A / Historical Context）"
                "2) 外部API（Agent B / Realtime News）。",
            ),
            (
                "human",
                "请针对用户问题生成报告，并保持以下结构：\n"
                "0. 用户问题\n"
                "1. 核心观点\n2. 基本面支撑\n3. 短期情绪扰动\n4. 风险提示\n\n"
                "5. 信息来源（必须分组）\n"
                "- 内部知识库（Agent A / Historical Context）\n"
                "- 外部API（Agent B / Realtime News）\n\n"
                f"user_query={user_query}\n"
                f"[Historical Context]={historical_context}\n"
                f"[Realtime News]={realtime_news}",
            ),
        ]
    )
    body = str(reply.content)

    if errors:
        body = "⚠️ 容错降级提示：外部数据源异常...\n\n" + body

    internal_status = "有数据" if historical_context else "无数据"
    external_status = "有数据" if realtime_news else "无数据"
    body += (
        "\n\n---\n"
        "### 数据来源分层标注\n"
        f"- 内部知识库（Agent A / Historical Context）：{internal_status}，条目数 {len(historical_context)}\n"
        f"- 外部API（Agent B / Realtime News）：{external_status}，条目数 {len(realtime_news)}"
    )

    logger.info(
        "✅ [Agent C] Exit | report_len=%s has_errors=%s",
        len(body),
        bool(errors),
    )
    return {
        "messages": [AIMessage(content=body)],
    }
