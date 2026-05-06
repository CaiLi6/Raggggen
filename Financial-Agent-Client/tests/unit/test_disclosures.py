"""Tests for safety/disclosures.py (task D5)."""

from __future__ import annotations

from safety.disclosures import default_risk_disclosure, NON_INVESTMENT_ADVICE
from reports.schema import RiskDisclosure


def test_default_disclosure_returns_risk_disclosure() -> None:
    d = default_risk_disclosure()
    assert isinstance(d, RiskDisclosure)


def test_default_disclosure_has_non_investment_advice() -> None:
    d = default_risk_disclosure()
    assert NON_INVESTMENT_ADVICE in d.non_investment_advice


def test_default_disclosure_has_risk_text() -> None:
    d = default_risk_disclosure()
    assert d.text
    assert "风险" in d.text


def test_default_disclosure_limitations_default_empty() -> None:
    d = default_risk_disclosure()
    assert d.limitations == []


def test_default_disclosure_with_limitations() -> None:
    limitations = ["数据时效限制", "行情数据为模拟"]
    d = default_risk_disclosure(limitations=limitations)
    assert d.limitations == limitations


def test_non_investment_advice_constant_present() -> None:
    assert "不构成投资建议" in NON_INVESTMENT_ADVICE
    assert "真实交易决策" in NON_INVESTMENT_ADVICE


def test_disclosure_text_mentions_market_risks() -> None:
    d = default_risk_disclosure()
    assert "金融市场" in d.text or "市场" in d.text
