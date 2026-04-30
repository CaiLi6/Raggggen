"""Build ContextBundle objects from tool outputs."""

from __future__ import annotations

from typing import Any

from context.bundle import ContextBundle
from context.source_map import SourceMap
from tools.records import ToolCallRecord


class ContextEngine:
    """Assemble query, history, tool results and source maps."""

    def __init__(self, token_budget: int = 6000):
        self.token_budget = token_budget

    def build(
        self,
        query: str,
        conversation: list[dict[str, str]],
        tool_outputs: dict[str, Any],
        tool_records: list[ToolCallRecord],
    ) -> ContextBundle:
        source_map = SourceMap()
        rag_chunks = self._normalize_rag(tool_outputs.get("rag_search"), source_map)
        news_items = self._normalize_news(tool_outputs.get("news_search"), source_map)
        market_snapshot = self._normalize_market(tool_outputs.get("market_data"))

        missing_data: list[str] = []
        if not rag_chunks:
            missing_data.append("内部知识库未返回可用材料。")
        if not news_items:
            missing_data.append("新闻舆情工具未返回可用材料。")
        if not market_snapshot:
            missing_data.append("行情摘要不可用。")

        tool_errors = [
            record.error_code or record.error_message or record.tool_name
            for record in tool_records
            if record.status == "error"
        ]
        for error in tool_errors:
            missing_data.append(f"工具异常: {error}")

        return ContextBundle(
            query=query,
            conversation=conversation[-8:],
            rag_chunks=rag_chunks,
            news_items=news_items,
            market_snapshot=market_snapshot,
            source_map=source_map.to_dict(),
            missing_data=missing_data,
            conflicts=[],
            token_budget=self.token_budget,
            tool_errors=tool_errors,
        )

    @staticmethod
    def _normalize_rag(data: Any, source_map: SourceMap) -> list[dict[str, Any]]:
        if not isinstance(data, dict):
            return []
        chunks = data.get("chunks") or []
        normalized: list[dict[str, Any]] = []
        for idx, chunk in enumerate(chunks, start=1):
            if not isinstance(chunk, dict):
                chunk = {"text": str(chunk)}
            title = str(chunk.get("title") or chunk.get("source") or f"Internal chunk {idx}")
            snippet = str(chunk.get("text") or chunk.get("content") or "")[:240]
            source = source_map.add(
                title=title,
                source_type="internal_knowledge",
                snippet=snippet,
                metadata={"tool": "rag_search", **dict(chunk.get("metadata") or {})},
            )
            merged = dict(chunk)
            merged["source_id"] = source.source_id
            normalized.append(merged)
        return normalized

    @staticmethod
    def _normalize_news(data: Any, source_map: SourceMap) -> list[dict[str, Any]]:
        if not isinstance(data, dict):
            return []
        items = data.get("results") or data.get("items") or []
        normalized: list[dict[str, Any]] = []
        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                item = {"title": f"News item {idx}", "content": str(item)}
            title = str(item.get("title") or item.get("url") or f"News item {idx}")
            url = item.get("url")
            snippet = str(item.get("content") or item.get("snippet") or item.get("raw_content") or "")[:240]
            source = source_map.add(
                title=title,
                source_type="external_news",
                url=str(url) if url else None,
                snippet=snippet,
                metadata={"tool": "news_search", "provider": data.get("provider", "unknown")},
            )
            merged = dict(item)
            merged["source_id"] = source.source_id
            normalized.append(merged)
        return normalized

    @staticmethod
    def _normalize_market(data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            return {}
        snapshot = data.get("snapshot") if isinstance(data.get("snapshot"), dict) else data
        if snapshot.get("error"):
            return {}
        return dict(snapshot)
