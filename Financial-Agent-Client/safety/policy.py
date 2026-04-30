"""Financial safety policy constants."""

from __future__ import annotations


PROHIBITED_QUERY_PATTERNS = [
    "帮我下单",
    "替我下单",
    "立即买入",
    "立即卖出",
    "执行买入",
    "执行卖出",
    "真实账户",
    "交易密码",
    "支付密码",
    "验证码",
    "保证收益",
    "稳赚",
    "无风险",
]

PROHIBITED_REPORT_PATTERNS = [
    "保证收益",
    "稳赚",
    "无风险",
    "必须买入",
    "必须卖出",
    "立即下单",
]
