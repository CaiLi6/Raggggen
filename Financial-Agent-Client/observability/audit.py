"""JSONL audit writer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SENSITIVE_KEYS = {"api_key", "token", "password", "secret", "credential", "验证码", "交易密码"}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if any(sensitive.lower() in key_text for sensitive in SENSITIVE_KEYS):
                cleaned[key] = "***REDACTED***"
            else:
                cleaned[key] = _redact(item)
        return cleaned
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


class JsonlTraceWriter:
    """Append traces to a local JSONL file."""

    def __init__(self, trace_dir: str | Path, file_name: str = "client_traces.jsonl"):
        self.path = Path(trace_dir) / file_name

    def write(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(_redact(payload), ensure_ascii=False)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
