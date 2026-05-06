"""Tests for config/loader.py (task A4)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from config.loader import ConfigLoader, DEFAULT_SETTINGS, _deep_merge


def test_default_settings_structure() -> None:
    loader = ConfigLoader()
    settings = loader.load_settings()
    assert "app" in settings
    assert "llm" in settings
    assert "tools" in settings
    assert "observability" in settings


def test_default_app_values() -> None:
    loader = ConfigLoader()
    settings = loader.load_settings()
    assert settings["app"]["name"] == "FinAgent OS Client"
    assert settings["app"]["token_budget"] == 6000


def test_default_llm_values() -> None:
    loader = ConfigLoader()
    settings = loader.load_settings()
    assert settings["llm"]["provider"] == "dashscope"


def test_deep_merge_overlay_overrides_base() -> None:
    base = {"a": 1, "b": {"x": 10, "y": 20}}
    overlay = {"b": {"y": 99}, "c": 3}
    merged = _deep_merge(base, overlay)
    assert merged["a"] == 1
    assert merged["b"]["x"] == 10
    assert merged["b"]["y"] == 99
    assert merged["c"] == 3


def test_deep_merge_does_not_mutate_base() -> None:
    base = {"a": {"x": 1}}
    overlay = {"a": {"x": 2}}
    merged = _deep_merge(base, overlay)
    assert base["a"]["x"] == 1
    assert merged["a"]["x"] == 2


def test_load_settings_env_override_mock_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINAGENT_MOCK_TOOLS", "true")
    loader = ConfigLoader()
    settings = loader.load_settings()
    assert settings["tools"]["mock_external"] is True


def test_load_settings_env_override_mock_tools_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINAGENT_MOCK_TOOLS", "0")
    loader = ConfigLoader()
    settings = loader.load_settings()
    assert settings["tools"]["mock_external"] is False


def test_load_tool_policy_raw_returns_dict() -> None:
    loader = ConfigLoader()
    raw = loader.load_tool_policy_raw()
    assert isinstance(raw, dict)


def test_read_prompt_returns_string() -> None:
    loader = ConfigLoader()
    prompt = loader.read_prompt("router")
    assert isinstance(prompt, str)


def test_read_prompt_missing_returns_empty() -> None:
    loader = ConfigLoader()
    result = loader.read_prompt("__nonexistent_prompt__")
    assert result == ""


def test_iter_agent_profile_files_returns_yaml_paths() -> None:
    loader = ConfigLoader()
    files = loader.iter_agent_profile_files()
    assert len(files) > 0
    for f in files:
        assert f.suffix == ".yaml"


def test_missing_config_root_returns_defaults(tmp_path: Path) -> None:
    loader = ConfigLoader(config_root=tmp_path / "empty_config")
    settings = loader.load_settings()
    assert settings["app"]["token_budget"] == 6000


def test_observability_trace_dir_is_absolute() -> None:
    loader = ConfigLoader()
    settings = loader.load_settings()
    trace_dir = settings["observability"]["trace_dir"]
    assert Path(trace_dir).is_absolute()
