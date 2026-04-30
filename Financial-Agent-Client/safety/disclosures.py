"""Risk disclosure builders."""

from __future__ import annotations

from reports.schema import RiskDisclosure


NON_INVESTMENT_ADVICE = (
    "本报告仅用于研究和信息整理，不构成投资建议、交易指令或收益承诺。"
    "任何真实交易决策都应由用户独立判断并承担风险。"
)


def default_risk_disclosure(limitations: list[str] | None = None) -> RiskDisclosure:
    return RiskDisclosure(
        text=(
            "金融市场存在价格波动、流动性、政策、行业周期、公司经营和数据时效性等风险。"
            "报告中的观点依赖当前可用来源，可能因新信息出现而变化。"
        ),
        non_investment_advice=NON_INVESTMENT_ADVICE,
        limitations=limitations or [],
    )
