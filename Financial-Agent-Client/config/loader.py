"""Load local settings, prompts and profile config for the client."""

from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = PROJECT_ROOT / "config"


DEFAULT_SETTINGS: dict[str, Any] = {
    "app": {
        "name": "FinAgent OS Client",
        "default_collection": "default",
        "default_output_format": "markdown",
        "token_budget": 6000,
    },
    "llm": {
        "provider": "dashscope",
        "router_model": "qwen-turbo",
        "report_model": "qwen-plus",
        "use_mock_without_key": True,
    },
    "tools": {
        "mock_external": False,
        "rag_top_k": 5,
        "rag_timeout_seconds": 90,
        "news_max_results": 3,
        "news_timeout_seconds": 20,
    },
    "observability": {
        "trace_dir": "logs",
        "client_trace_file": "client_traces.jsonl",
        "write_jsonl": True,
    },
}


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml
    except Exception:
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class ConfigLoader:
    """Load YAML config with environment variable overrides."""

    def __init__(self, config_root: Path | str | None = None):
        self.config_root = Path(config_root) if config_root else CONFIG_ROOT

    def load_settings(self) -> dict[str, Any]:
        loaded = _load_yaml_file(self.config_root / "client_settings.yaml")
        settings = _deep_merge(DEFAULT_SETTINGS, loaded)

        llm = settings.setdefault("llm", {})
        tools = settings.setdefault("tools", {})
        observability = settings.setdefault("observability", {})

        llm["router_model"] = os.getenv("DASHSCOPE_ROUTER_MODEL", llm.get("router_model"))
        llm["report_model"] = os.getenv("DASHSCOPE_MODEL", llm.get("report_model"))
        llm["use_mock_without_key"] = _env_bool(
            "FINAGENT_USE_MOCK_WITHOUT_KEY",
            bool(llm.get("use_mock_without_key", True)),
        )

        tools["mock_external"] = _env_bool(
            "FINAGENT_MOCK_TOOLS",
            bool(tools.get("mock_external", False)),
        )
        if os.getenv("RAG_SERVER_PATH"):
            tools["rag_server_path"] = os.getenv("RAG_SERVER_PATH")
        if os.getenv("RAG_PYTHON_PATH"):
            tools["rag_python_path"] = os.getenv("RAG_PYTHON_PATH")

        trace_dir = Path(str(observability.get("trace_dir", "logs")))
        if not trace_dir.is_absolute():
            trace_dir = PROJECT_ROOT / trace_dir
        observability["trace_dir"] = str(trace_dir)
        return settings

    def load_tool_policy_raw(self) -> dict[str, Any]:
        return _load_yaml_file(self.config_root / "tool_policy.yaml")

    def read_prompt(self, name: str) -> str:
        path = self.config_root / "prompts" / f"{name}.md"
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def iter_agent_profile_files(self) -> list[Path]:
        profile_dir = self.config_root / "agents"
        if not profile_dir.exists():
            return []
        return sorted(profile_dir.glob("*.yaml"))

    def load_yaml(self, path: Path) -> dict[str, Any]:
        return _load_yaml_file(path)
