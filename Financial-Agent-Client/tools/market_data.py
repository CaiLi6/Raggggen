"""Market data provider interface and mock implementation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol


class MarketDataProvider(Protocol):
    def snapshot(self, query: str) -> dict[str, Any]:
        ...


@dataclass
class MockMarketDataProvider:
    """Mock provider used until a real market data provider is configured."""

    provider_name: str = "mock_market_data"

    def snapshot(self, query: str) -> dict[str, Any]:
        symbols = self._extract_symbols(query)
        return {
            "provider": self.provider_name,
            "symbols": symbols,
            "as_of": "mock-latest",
            "summary": (
                "Mock snapshot only. Use a real provider before relying on price, volume "
                "or valuation conclusions."
            ),
            "observations": [
                "行情数据为模拟值，不能作为真实交易依据。",
                "建议补充真实价格、成交量、估值分位和财务指标后复核。",
            ],
        }

    @staticmethod
    def _extract_symbols(query: str) -> list[str]:
        candidates = re.findall(r"\b[A-Z]{1,5}\b|\b\d{6}\b", query or "")
        return candidates[:5] or ["UNSPECIFIED"]


class MarketDataAdapter:
    def __init__(self, provider: MarketDataProvider | None = None):
        self.provider = provider or MockMarketDataProvider()

    def __call__(self, query: str) -> dict[str, Any]:
        try:
            return {"snapshot": self.provider.snapshot(query)}
        except Exception as exc:
            return {"snapshot": {}, "error": "MARKET_DATA_UNAVAILABLE", "message": str(exc)}
