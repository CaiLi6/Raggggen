"""Tests for tools/market_data.py (task E3)."""

from __future__ import annotations

from tools.market_data import MarketDataAdapter, MockMarketDataProvider


def test_mock_provider_returns_snapshot() -> None:
    provider = MockMarketDataProvider()
    snap = provider.snapshot("分析 AAPL")
    assert isinstance(snap, dict)
    assert snap.get("provider") == "mock_market_data"


def test_mock_provider_extracts_ticker_symbols() -> None:
    provider = MockMarketDataProvider()
    snap = provider.snapshot("Analyze AAPL and TSLA")
    symbols = snap.get("symbols", [])
    assert "AAPL" in symbols
    assert "TSLA" in symbols


def test_mock_provider_extracts_cn_stock_code() -> None:
    provider = MockMarketDataProvider()
    snap = provider.snapshot("分析 600036 招商银行")
    symbols = snap.get("symbols", [])
    assert "600036" in symbols


def test_mock_provider_fallback_symbol_unspecified() -> None:
    provider = MockMarketDataProvider()
    snap = provider.snapshot("请分析一下市场")
    symbols = snap.get("symbols", [])
    assert symbols == ["UNSPECIFIED"]


def test_mock_provider_has_observations() -> None:
    provider = MockMarketDataProvider()
    snap = provider.snapshot("AAPL")
    assert "observations" in snap
    assert len(snap["observations"]) > 0


def test_mock_provider_has_mock_disclaimer() -> None:
    provider = MockMarketDataProvider()
    snap = provider.snapshot("AAPL")
    assert "Mock" in snap.get("summary", "")


def test_adapter_default_uses_mock_provider() -> None:
    adapter = MarketDataAdapter()
    result = adapter("AAPL")
    assert "snapshot" in result
    assert result["snapshot"].get("provider") == "mock_market_data"


def test_adapter_wraps_provider_error() -> None:
    class FailingProvider:
        def snapshot(self, query: str):
            raise RuntimeError("connection failed")

    adapter = MarketDataAdapter(provider=FailingProvider())
    result = adapter("q")
    assert result.get("error") == "MARKET_DATA_UNAVAILABLE"
    assert "connection failed" in result.get("message", "")
    assert result.get("snapshot") == {}


def test_adapter_snapshot_nested_in_snapshot_key() -> None:
    adapter = MarketDataAdapter()
    result = adapter("TSLA")
    assert isinstance(result["snapshot"], dict)
