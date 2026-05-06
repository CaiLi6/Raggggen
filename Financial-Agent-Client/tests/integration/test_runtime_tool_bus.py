"""Integration tests for Runtime + Tool Bus (task E4)."""

from __future__ import annotations

import asyncio

from tools import create_default_tool_bus
from tools.bus import RetryConfig, ToolBus, _is_retryable
from tools.policy import ToolPolicy


def run(coro):
    return asyncio.run(coro)


def test_default_tool_bus_registers_expected_tools() -> None:
    bus = create_default_tool_bus(mock_tools=True)
    tools = bus.list_tools()
    assert "rag_search" in tools
    assert "news_search" in tools
    assert "market_data" in tools
    assert "evaluate_report" in tools


def test_rag_search_via_bus_mock() -> None:
    bus = create_default_tool_bus(mock_tools=True)
    result = run(bus.call("rag_search", {"query": "AAPL财报"}))
    assert result.record.status == "success"
    assert "chunks" in result.data


def test_news_search_via_bus_mock() -> None:
    bus = create_default_tool_bus(mock_tools=True)
    result = run(bus.call("news_search", {"query": "市场新闻"}))
    assert result.record.status == "success"
    assert "results" in result.data


def test_market_data_via_bus() -> None:
    bus = create_default_tool_bus(mock_tools=True)
    result = run(bus.call("market_data", {"query": "TSLA股价"}))
    assert result.record.status == "success"
    assert "snapshot" in result.data


def test_evaluate_report_via_bus() -> None:
    bus = create_default_tool_bus(mock_tools=True)
    result = run(bus.call(
        "evaluate_report",
        {"query": "q", "report_markdown": "# Report\n风险\n不构成投资建议"},
    ))
    assert result.record.status == "success"
    assert "overall" in result.data


def test_denied_tool_returns_policy_denied_error() -> None:
    bus = create_default_tool_bus(mock_tools=True)

    async def fake_handler(**kwargs):
        return {}

    bus.register("broker_order", fake_handler)
    result = run(bus.call("broker_order", {}))
    assert result.record.status == "error"
    assert result.record.error_code == "POLICY_DENIED"


def test_bus_records_are_stored() -> None:
    bus = create_default_tool_bus(mock_tools=True)
    run(bus.call("rag_search", {"query": "q"}))
    run(bus.call("news_search", {"query": "q"}))
    assert len(bus.records) == 2


def test_bus_records_contain_tool_names() -> None:
    bus = create_default_tool_bus(mock_tools=True)
    run(bus.call("rag_search", {"query": "q"}))
    assert bus.records[0].tool_name == "rag_search"


def test_unknown_tool_returns_error_record() -> None:
    bus = create_default_tool_bus(mock_tools=True)
    result = run(bus.call("nonexistent_tool", {}))
    assert result.record.status == "error"
    assert result.record.error_code is not None


# ── Retry behaviour ──────────────────────────────────────────────────────────

def test_is_retryable_on_os_error() -> None:
    assert _is_retryable(OSError("connection reset")) is True


def test_is_retryable_false_on_timeout() -> None:
    assert _is_retryable(TimeoutError("timed out")) is False


def test_is_retryable_false_on_value_error() -> None:
    assert _is_retryable(ValueError("bad input")) is False


def test_retry_config_defaults() -> None:
    cfg = RetryConfig()
    assert cfg.max_attempts == 3
    assert cfg.wait_min == 0.5
    assert cfg.wait_max == 4.0


def test_retry_config_custom() -> None:
    cfg = RetryConfig(max_attempts=5, wait_min=0.1, wait_max=2.0)
    assert cfg.max_attempts == 5


def test_bus_accepts_retry_config() -> None:
    cfg = RetryConfig(max_attempts=2, wait_min=0.0, wait_max=0.0)
    bus = ToolBus(retry_config=cfg)
    assert bus.retry_config.max_attempts == 2


def test_successful_call_records_attempt_count_one() -> None:
    """A first-attempt success should record attempt_count=1."""
    bus = create_default_tool_bus(mock_tools=True)
    result = run(bus.call("rag_search", {"query": "AAPL"}))
    assert result.record.attempt_count == 1


def test_retry_succeeds_on_second_attempt() -> None:
    """Handler that raises OSError once then succeeds → attempt_count=2."""
    no_wait = RetryConfig(max_attempts=3, wait_min=0.0, wait_max=0.0)
    permissive = ToolPolicy(allowed_tools=set())  # empty = no allowlist restriction
    bus = ToolBus(policy=permissive, retry_config=no_wait)
    call_count = 0

    async def flaky_handler(**_):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise OSError("transient network error")
        return {"chunks": []}

    bus.register("flaky_tool", flaky_handler)
    result = run(bus.call("flaky_tool", {}))
    assert result.record.status == "success"
    assert call_count == 2
    assert result.record.attempt_count == 2


def test_timeout_is_not_retried() -> None:
    """TimeoutError must not trigger retry — handler called exactly once."""
    no_wait = RetryConfig(max_attempts=3, wait_min=0.0, wait_max=0.0)
    permissive = ToolPolicy(allowed_tools=set())
    bus = ToolBus(policy=permissive, retry_config=no_wait)
    call_count = 0

    async def always_times_out(**_):
        nonlocal call_count
        call_count += 1
        raise TimeoutError("timeout")

    bus.register("slow_tool", always_times_out)
    result = run(bus.call("slow_tool", {}))
    assert result.record.status == "error"
    assert "TIMEOUT" in (result.record.error_code or "")
    assert call_count == 1  # no retries on timeout


def test_non_retryable_error_propagates_immediately() -> None:
    """ValueError is not retryable → handler called once, error recorded."""
    no_wait = RetryConfig(max_attempts=3, wait_min=0.0, wait_max=0.0)
    permissive = ToolPolicy(allowed_tools=set())
    bus = ToolBus(policy=permissive, retry_config=no_wait)
    call_count = 0

    async def bad_handler(**_):
        nonlocal call_count
        call_count += 1
        raise ValueError("invalid input")

    bus.register("bad_tool", bad_handler)
    result = run(bus.call("bad_tool", {}))
    assert result.record.status == "error"
    assert result.record.error_code == "UNKNOWN_ERROR"
    assert call_count == 1  # not retried


def test_all_retries_exhausted_returns_error() -> None:
    """Handler raises OSError on all attempts → error record returned."""
    no_wait = RetryConfig(max_attempts=3, wait_min=0.0, wait_max=0.0)
    permissive = ToolPolicy(allowed_tools=set())
    bus = ToolBus(policy=permissive, retry_config=no_wait)
    call_count = 0

    async def always_fails(**_):
        nonlocal call_count
        call_count += 1
        raise OSError("persistent network failure")

    bus.register("broken_tool", always_fails)
    result = run(bus.call("broken_tool", {}))
    assert result.record.status == "error"
    assert call_count == 3  # retried up to max_attempts
