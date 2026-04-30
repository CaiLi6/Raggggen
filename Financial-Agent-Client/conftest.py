"""Pytest configuration for FinAgent OS Client."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def pytest_configure(config):
    config.addinivalue_line("markers", "llm: tests that call real or semi-real LLM providers")
    config.addinivalue_line("markers", "external: tests that call real external providers")
    config.addinivalue_line("markers", "e2e: end-to-end smoke tests")
    config.addinivalue_line("markers", "slow: slow tests")
