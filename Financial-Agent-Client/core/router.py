"""Compatibility intent router."""

from __future__ import annotations

from agents.router_agent import RouterAgent


def intent_router(query: str) -> str:
    return RouterAgent().route(query).intent
