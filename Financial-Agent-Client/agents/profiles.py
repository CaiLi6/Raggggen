"""Agent profile loading."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from config.loader import ConfigLoader


DEFAULT_PROFILE_NAMES = [
    "router",
    "fundamental",
    "sentiment",
    "risk",
    "chief_analyst",
    "compliance",
]


@dataclass
class AgentProfile:
    name: str
    role: str
    prompt: str = ""
    allowed_tools: list[str] = field(default_factory=list)
    output_contract: str = ""
    safety_boundary: str = "research_only"


def _fallback_profiles() -> dict[str, AgentProfile]:
    roles = {
        "router": "Router Agent",
        "fundamental": "Fundamental Analyst",
        "sentiment": "Sentiment Analyst",
        "risk": "Risk Analyst",
        "chief_analyst": "Chief Analyst",
        "compliance": "Compliance Reviewer",
    }
    tools = {
        "fundamental": ["rag_search"],
        "sentiment": ["news_search"],
    }
    return {
        name: AgentProfile(
            name=name,
            role=roles[name],
            prompt=name,
            allowed_tools=tools.get(name, []),
            output_contract=name,
        )
        for name in DEFAULT_PROFILE_NAMES
    }


def load_agent_profiles(loader: ConfigLoader | None = None) -> dict[str, AgentProfile]:
    loader = loader or ConfigLoader()
    profiles: dict[str, AgentProfile] = {}
    for path in loader.iter_agent_profile_files():
        raw = loader.load_yaml(path)
        if not raw:
            continue
        profile = AgentProfile(
            name=str(raw.get("name") or path.stem),
            role=str(raw.get("role") or path.stem),
            prompt=str(raw.get("prompt") or path.stem),
            allowed_tools=list(raw.get("allowed_tools") or []),
            output_contract=str(raw.get("output_contract") or ""),
            safety_boundary=str(raw.get("safety_boundary") or "research_only"),
        )
        profiles[profile.name] = profile
    fallback = _fallback_profiles()
    fallback.update(profiles)
    return fallback
