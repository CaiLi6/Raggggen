"""Tests for tools/policy.py (task D1)."""

from __future__ import annotations

import pytest

from tools.policy import ToolPolicy, DEFAULT_ALLOWED_TOOLS, DEFAULT_DENIED_TOOLS


def test_default_policy_allows_rag_search() -> None:
    policy = ToolPolicy()
    assert policy.is_allowed("rag_search") is True


def test_default_policy_allows_news_search() -> None:
    policy = ToolPolicy()
    assert policy.is_allowed("news_search") is True


def test_default_policy_allows_market_data() -> None:
    policy = ToolPolicy()
    assert policy.is_allowed("market_data") is True


def test_default_policy_allows_evaluate_report() -> None:
    policy = ToolPolicy()
    assert policy.is_allowed("evaluate_report") is True


def test_default_policy_denies_broker_order() -> None:
    policy = ToolPolicy()
    assert policy.is_allowed("broker_order") is False


def test_default_policy_denies_bank_transfer() -> None:
    policy = ToolPolicy()
    assert policy.is_allowed("bank_transfer") is False


def test_default_policy_denies_payment() -> None:
    policy = ToolPolicy()
    assert policy.is_allowed("payment") is False


def test_default_policy_denies_credential_reader() -> None:
    policy = ToolPolicy()
    assert policy.is_allowed("credential_reader") is False


def test_require_allowed_raises_for_denied_tool() -> None:
    policy = ToolPolicy()
    with pytest.raises(PermissionError, match="broker_order"):
        policy.require_allowed("broker_order")


def test_require_allowed_passes_for_allowed_tool() -> None:
    policy = ToolPolicy()
    policy.require_allowed("rag_search")


def test_from_raw_with_custom_allowed() -> None:
    raw = {"allowed_tools": ["rag_search", "custom_tool"]}
    policy = ToolPolicy.from_raw(raw)
    assert policy.is_allowed("custom_tool") is True
    assert policy.is_allowed("news_search") is False


def test_from_raw_with_custom_denied() -> None:
    raw = {"denied_tools": ["rag_search"]}
    policy = ToolPolicy.from_raw(raw)
    assert policy.is_allowed("rag_search") is False


def test_from_raw_empty_dict_uses_defaults() -> None:
    policy = ToolPolicy.from_raw({})
    for tool in DEFAULT_ALLOWED_TOOLS:
        assert policy.is_allowed(tool) is True
    for tool in DEFAULT_DENIED_TOOLS:
        assert policy.is_allowed(tool) is False


def test_from_raw_none_uses_defaults() -> None:
    policy = ToolPolicy.from_raw(None)
    assert policy.is_allowed("rag_search") is True


def test_tool_not_in_allowed_set_is_denied() -> None:
    policy = ToolPolicy(allowed_tools={"rag_search"})
    assert policy.is_allowed("unknown_tool") is False


def test_prohibited_actions_set() -> None:
    policy = ToolPolicy(prohibited_actions={"execute_trade"})
    assert "execute_trade" in policy.prohibited_actions
