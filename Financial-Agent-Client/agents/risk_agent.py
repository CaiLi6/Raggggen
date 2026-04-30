"""Risk Analyst Agent."""

from __future__ import annotations

from typing import Any

from context.bundle import ContextBundle


class RiskAnalystAgent:
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        bundle: ContextBundle = state["context_bundle"]
        risks = [
            "市场价格可能受宏观流动性、政策变化、行业竞争和风险偏好波动影响。",
            "当前结论依赖已返回来源，数据缺口会降低判断置信度。",
        ]
        for error in bundle.tool_errors:
            risks.append(f"工具异常可能影响结论完整性: {error}")
        for missing in bundle.missing_data:
            risks.append(missing)
        state["risk_findings"] = risks
        return state
