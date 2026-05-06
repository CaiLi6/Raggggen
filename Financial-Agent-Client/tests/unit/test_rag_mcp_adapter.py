"""Tests for tools/rag_mcp.py (task E1)."""

from __future__ import annotations

import asyncio

import pytest

from tools.rag_mcp import RAGMCPAdapter


def run(coro):
    return asyncio.run(coro)


def test_mock_mode_returns_chunks() -> None:
    adapter = RAGMCPAdapter(mock=True)
    result = run(adapter("test query"))
    assert "chunks" in result
    assert len(result["chunks"]) >= 1


def test_mock_mode_chunk_contains_text() -> None:
    adapter = RAGMCPAdapter(mock=True)
    result = run(adapter("苹果公司财报"))
    chunk = result["chunks"][0]
    assert "text" in chunk
    assert "苹果公司财报" in chunk["text"]


def test_mock_mode_returns_correct_collection() -> None:
    adapter = RAGMCPAdapter(mock=True)
    result = run(adapter("q", collection="finance_docs"))
    assert result.get("collection") == "finance_docs"


def test_mock_mode_provider_is_mock_rag() -> None:
    adapter = RAGMCPAdapter(mock=True)
    result = run(adapter("q"))
    assert result.get("provider") == "mock_rag"


def test_no_key_falls_back_gracefully() -> None:
    """Without real MCP server, should return error dict rather than crash."""
    adapter = RAGMCPAdapter(mock=False)
    result = run(adapter("q"))
    # Should either succeed (if infra available) or return error dict
    if "error" in result:
        assert "chunks" in result
        assert result["chunks"] == []
    else:
        assert "chunks" in result


def test_mock_default_collection_is_default() -> None:
    adapter = RAGMCPAdapter(mock=True)
    result = run(adapter("q"))
    assert result.get("collection") == "default"


def test_error_map_rag_tool_missing() -> None:
    from tools.rag_mcp import _map_error
    assert _map_error("TOOL_MISSING") == "RAG_TOOL_MISSING"


def test_error_map_timeout() -> None:
    from tools.rag_mcp import _map_error
    assert _map_error("TIMEOUT") == "RAG_TIMEOUT"


def test_error_map_empty_result() -> None:
    from tools.rag_mcp import _map_error
    assert _map_error("EMPTY_RESULT") == "RAG_EMPTY_RESULT"


def test_error_map_unknown() -> None:
    from tools.rag_mcp import _map_error
    assert _map_error("SOMETHING_ELSE") == "RAG_SERVER_UNAVAILABLE"
