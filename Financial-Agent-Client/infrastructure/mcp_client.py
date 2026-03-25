"""Minimal MCP stdio client wrapper with lifecycle management."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class MCPClientConfig:
    """Configuration for launching the MCP server process."""

    command: str = "python"
    args: list[str] | None = None
    cwd: str | None = None


class MCPStdioClient:
    """Manage an MCP server subprocess via stdio as a context manager."""

    def __init__(self, config: MCPClientConfig | None = None):
        self.config = config or MCPClientConfig(
            command=os.getenv("MCP_SERVER_COMMAND", "python"),
            args=[
                os.getenv("MCP_SERVER_ENTRY", "main.py"),
            ],
            cwd=os.getenv("MCP_SERVER_CWD"),
        )
        self._proc: subprocess.Popen[str] | None = None
        self._request_id = 0

    def start(self) -> None:
        if self._proc and self._proc.poll() is None:
            return

        args = self.config.args or []
        self._proc = subprocess.Popen(
            [self.config.command, *args],
            cwd=self.config.cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def stop(self) -> None:
        if not self._proc:
            return
        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None

    def __enter__(self) -> "MCPStdioClient":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def call_tool(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Send a JSON-RPC style request over stdio and return raw response text.

        This function stays lightweight for this project phase and is resilient when
        the server does not answer as expected.
        """
        if not self._proc or self._proc.poll() is not None:
            raise RuntimeError("MCP server process is not running")
        if not self._proc.stdin or not self._proc.stdout:
            raise RuntimeError("MCP stdio pipes are unavailable")

        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": tool_input},
        }
        self._proc.stdin.write(json.dumps(payload, ensure_ascii=True) + "\n")
        self._proc.stdin.flush()
        response_line = self._proc.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from MCP server")
        return response_line.strip()
