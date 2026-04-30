"""RAG MCP adapter for query_knowledge_hub."""

from __future__ import annotations

import os
from typing import Any


def _map_error(text: str) -> str:
    if "TOOL_MISSING" in text:
        return "RAG_TOOL_MISSING"
    if "TIMEOUT" in text or "超时" in text:
        return "RAG_TIMEOUT"
    if "EMPTY_RESULT" in text:
        return "RAG_EMPTY_RESULT"
    return "RAG_SERVER_UNAVAILABLE"


class RAGMCPAdapter:
    def __init__(self, mock: bool = False, top_k: int = 5):
        self.mock = mock
        self.top_k = top_k

    async def __call__(
        self,
        query: str,
        collection: str | None = "default",
        top_k: int | None = None,
    ) -> dict[str, Any]:
        if self.mock:
            return {
                "provider": "mock_rag",
                "collection": collection,
                "chunks": [
                    {
                        "title": "Mock internal research note",
                        "text": f"内部知识库模拟材料：围绕“{query}”提供财务、业务和管理层讨论摘要。",
                        "metadata": {"collection": collection or "default"},
                    }
                ],
            }

        try:
            from infrastructure.tools import get_rag_context

            text = await get_rag_context(
                query=query,
                top_k=top_k or self.top_k,
                collection=collection or "default",
            )
        except Exception as exc:
            return {"error": "RAG_SERVER_UNAVAILABLE", "message": str(exc), "chunks": []}

        if text.startswith("MCP_"):
            return {"error": _map_error(text), "message": text, "chunks": []}
        if not text.strip():
            return {"error": "RAG_EMPTY_RESULT", "message": "RAG returned empty result", "chunks": []}
        return {
            "provider": "rag_mcp",
            "collection": collection,
            "chunks": [
                {
                    "title": "Internal knowledge hub result",
                    "text": text,
                    "metadata": {"collection": collection or "default"},
                }
            ],
        }


def should_use_mock_without_server() -> bool:
    return os.getenv("FINAGENT_MOCK_TOOLS", "").lower() in {"1", "true", "yes", "on"}
