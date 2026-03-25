"""Tool wrappers for MCP knowledge queries and sentiment research."""

from __future__ import annotations

import asyncio
import logging
import os
import traceback
from datetime import timedelta
from pathlib import Path
from typing import Any

from langchain_community.tools.tavily_search import TavilySearchResults
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.shared.exceptions import McpError

from infrastructure.mcp_client import MCPStdioClient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


RAG_SERVER_PATH = Path(
    r"C:\Users\Lenovo\Desktop\gaoren\gaoren\Modular RAG MCP Server\MODULAR-RAG-MCP-SERVER\src\mcp_server\server.py"
)
RAG_PYTHON_PATH = Path(
    r"C:\Users\Lenovo\Desktop\gaoren\gaoren\Modular RAG MCP Server\MODULAR-RAG-MCP-SERVER\.venv\Scripts\python.exe"
)
RAG_TIMEOUT_SECONDS = 90
TAVILY_TIMEOUT_SECONDS = 20


def _resolve_rag_server_script() -> Path:
    """Resolve RAG server entry script from configured absolute path."""
    return RAG_SERVER_PATH.resolve()


async def get_rag_context(
    query: str,
    top_k: int = 5,
    collection: str | None = "default",
) -> str:
    """Get historical context from adjacent RAG MCP server via stdio_client."""
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        logger.info("[RAG Tool] Empty query received; skip MCP call.")
        return "MCP_SERVER_UNAVAILABLE"

    server_script = _resolve_rag_server_script()
    rag_root = server_script.parent.parent.parent.resolve()
    args = [str(server_script)]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(rag_root)
    server_params = StdioServerParameters(
        command=str(RAG_PYTHON_PATH),
        args=args,
        cwd=rag_root,
        env=env,
    )

    try:
        logger.info("[RAG Tool] Start query_knowledge_hub | query=%s | top_k=%s", cleaned_query, top_k)
        call_args: dict[str, Any] = {"query": cleaned_query, "top_k": top_k}
        if collection:
            call_args["collection"] = collection

        # Use local context managers per invocation to avoid cross-task cleanup issues.
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                available_tools = {tool.name for tool in tools.tools}
                if "query_knowledge_hub" not in available_tools:
                    return "MCP_CONNECTED_BUT_TOOL_MISSING"

                result = await session.call_tool(
                    "query_knowledge_hub",
                    arguments=call_args,
                    read_timeout_seconds=timedelta(seconds=RAG_TIMEOUT_SECONDS),
                )

        texts: list[str] = []
        for block in result.content:
            text_value = getattr(block, "text", None)
            if text_value:
                texts.append(str(text_value))
        if texts:
            response_text = "\n".join(texts)
        elif getattr(result, "isError", False):
            response_text = "MCP_CONNECTED_BUT_TOOL_ERROR"
        else:
            response_text = "MCP_CONNECTED_BUT_EMPTY_RESULT"

        logger.info("[RAG Tool] Finished query_knowledge_hub | result_len=%s", len(response_text))
        return response_text
    except McpError as exc:
        logger.exception("[RAG Tool] McpError | query=%s", cleaned_query)
        if "Timed out" in str(exc):
            return "MCP_CONNECTED_BUT_QUERY_TIMEOUT: 工具调用超时"
        return f"MCP_SERVER_UNAVAILABLE: {exc}"
    except Exception as exc:
        logger.exception("[RAG Tool] Unexpected error | query=%s", cleaned_query)
        error_text = str(exc)
        if "Timed out" in error_text or "deadline exceeded" in error_text:
            return "MCP_CONNECTED_BUT_QUERY_TIMEOUT: 工具调用超时"
        return "MCP_SERVER_UNAVAILABLE: " + " | ".join(
            traceback.format_exception_only(type(exc), exc)
        ).strip()


def mcp_query_knowledge_hub(query: str, client: MCPStdioClient | None = None) -> str:
    """Compatibility wrapper; prefer get_rag_context in async agent nodes."""
    if client is not None:
        try:
            return client.call_tool("query_knowledge_hub", {"query": query})
        except Exception:
            return "MCP_SERVER_UNAVAILABLE"
    return asyncio.run(get_rag_context(query=query))


async def web_search_sentiment(query: str) -> dict[str, Any]:
    """Run real-time sentiment/news search via Tavily."""
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        logger.info("[Tavily Tool] Empty query received; skip search.")
        return {
            "query": query,
            "provider": "tavily",
            "results": [],
            "error": "WEB_SEARCH_FAILED",
        }

    try:
        logger.info("[Tavily Tool] Start search | query=%s", cleaned_query)
        search = TavilySearchResults(
            max_results=3,
            tavily_api_key=os.getenv("TAVILY_API_KEY"),
        )
        results = await asyncio.wait_for(
            asyncio.to_thread(search.invoke, cleaned_query),
            timeout=TAVILY_TIMEOUT_SECONDS,
        )
        logger.info(
            "[Tavily Tool] Finished search | result_count=%s",
            len(results) if isinstance(results, list) else 1,
        )
        return {
            "query": cleaned_query,
            "provider": "tavily",
            "results": results,
        }
    except TimeoutError:
        logger.exception(
            "[Tavily Tool] Timeout after %ss | query=%s",
            TAVILY_TIMEOUT_SECONDS,
            cleaned_query,
        )
        return {
            "query": cleaned_query,
            "provider": "tavily",
            "results": [],
            "error": "WEB_SEARCH_FAILED",
            "message": "工具调用超时",
        }
    except Exception:
        logger.exception("[Tavily Tool] Unexpected error | query=%s", cleaned_query)
        return {
            "query": cleaned_query,
            "provider": "tavily",
            "results": [],
            "error": "WEB_SEARCH_FAILED",
        }
