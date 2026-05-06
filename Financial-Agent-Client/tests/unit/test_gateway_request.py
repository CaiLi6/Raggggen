"""Tests for gateway/request.py (task B1)."""

from __future__ import annotations

import pytest

from gateway.request import GatewayRequest


def test_from_ui_sets_markdown_format() -> None:
    req = GatewayRequest.from_ui("分析宁德时代")
    assert req.output_format == "markdown"


def test_from_ui_passes_metadata() -> None:
    req = GatewayRequest.from_ui("query", metadata={"key": "val"})
    assert req.metadata["key"] == "val"


def test_from_ui_default_metadata_is_empty() -> None:
    req = GatewayRequest.from_ui("query")
    assert req.metadata == {}


def test_from_cli_sets_mock_tools() -> None:
    req = GatewayRequest.from_cli("query", mock_tools=True)
    assert req.metadata["mock_tools"] is True


def test_from_cli_sets_json_format() -> None:
    req = GatewayRequest.from_cli("query", output_format="json")
    assert req.output_format == "json"


def test_from_cli_default_mock_tools_false() -> None:
    req = GatewayRequest.from_cli("query")
    assert req.metadata.get("mock_tools") is False


def test_validate_raises_on_empty_query() -> None:
    with pytest.raises(ValueError, match="query must not be empty"):
        GatewayRequest(query="").validate()


def test_validate_raises_on_whitespace_query() -> None:
    with pytest.raises(ValueError, match="query must not be empty"):
        GatewayRequest(query="   ").validate()


def test_validate_raises_on_invalid_format() -> None:
    with pytest.raises(ValueError, match="output_format"):
        GatewayRequest(query="test", output_format="html").validate()


def test_validate_passes_for_valid_request() -> None:
    req = GatewayRequest.from_cli("分析 AAPL")
    req.validate()


def test_normalized_query_strips_whitespace() -> None:
    req = GatewayRequest(query="  hello world  ")
    assert req.normalized_query == "hello world"


def test_thread_id_defaults_to_none() -> None:
    req = GatewayRequest(query="q")
    assert req.thread_id is None


def test_collection_defaults_to_none() -> None:
    req = GatewayRequest(query="q")
    assert req.collection is None


def test_enable_eval_defaults_to_false() -> None:
    req = GatewayRequest(query="q")
    assert req.enable_eval is False
