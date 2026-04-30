from __future__ import annotations

import asyncio

from tools.bus import ToolBus
from tools.policy import ToolPolicy


def test_tool_bus_records_success() -> None:
    bus = ToolBus(policy=ToolPolicy(allowed_tools={"echo"}))
    bus.register("echo", lambda value: {"value": value})

    result = asyncio.run(bus.call("echo", {"value": "ok"}, role="test"))

    assert result.data == {"value": "ok"}
    assert result.record.status == "success"
    assert result.record.role == "test"


def test_tool_bus_policy_denial_is_recorded() -> None:
    bus = ToolBus(policy=ToolPolicy(allowed_tools={"safe"}, denied_tools={"unsafe"}))

    result = asyncio.run(bus.call("unsafe", {}, role="test"))

    assert result.data["error"] == "POLICY_DENIED"
    assert result.record.status == "error"
    assert result.record.error_code == "POLICY_DENIED"
