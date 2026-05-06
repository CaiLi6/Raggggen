"""Tests for agents/profiles.py (task F1)."""

from __future__ import annotations

from agents.profiles import (
    AgentProfile,
    load_agent_profiles,
    DEFAULT_PROFILE_NAMES,
)


def test_load_agent_profiles_returns_dict() -> None:
    profiles = load_agent_profiles()
    assert isinstance(profiles, dict)


def test_load_agent_profiles_contains_all_defaults() -> None:
    profiles = load_agent_profiles()
    for name in DEFAULT_PROFILE_NAMES:
        assert name in profiles, f"Profile '{name}' missing"


def test_profiles_are_agent_profile_instances() -> None:
    profiles = load_agent_profiles()
    for name, profile in profiles.items():
        assert isinstance(profile, AgentProfile), f"{name} is not AgentProfile"


def test_router_profile_has_role() -> None:
    profiles = load_agent_profiles()
    assert profiles["router"].role


def test_fundamental_profile_allows_rag_search() -> None:
    profiles = load_agent_profiles()
    assert "rag_search" in profiles["fundamental"].allowed_tools


def test_sentiment_profile_allows_news_search() -> None:
    profiles = load_agent_profiles()
    assert "news_search" in profiles["sentiment"].allowed_tools


def test_safety_boundary_is_research_only() -> None:
    profiles = load_agent_profiles()
    for profile in profiles.values():
        assert profile.safety_boundary == "research_only"


def test_profile_name_matches_key() -> None:
    profiles = load_agent_profiles()
    for key, profile in profiles.items():
        assert profile.name == key


def test_agent_profile_dataclass_fields() -> None:
    p = AgentProfile(name="test", role="Test Role")
    assert p.name == "test"
    assert p.role == "Test Role"
    assert p.prompt == ""
    assert p.allowed_tools == []
    assert p.safety_boundary == "research_only"
