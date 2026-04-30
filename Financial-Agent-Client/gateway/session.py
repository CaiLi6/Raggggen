"""In-memory session management for Gateway requests."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class SessionState:
    thread_id: str
    history: list[dict[str, str]] = field(default_factory=list)


class SessionManager:
    """Small local session store keyed by thread id."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    @staticmethod
    def new_thread_id(prefix: str = "thread") -> str:
        return f"{prefix}-{uuid.uuid4().hex[:8]}"

    def get_or_create(self, thread_id: str | None = None) -> SessionState:
        active_thread = thread_id or self.new_thread_id()
        if active_thread not in self._sessions:
            self._sessions[active_thread] = SessionState(thread_id=active_thread)
        return self._sessions[active_thread]

    def append(self, thread_id: str, role: str, content: str) -> None:
        session = self.get_or_create(thread_id)
        session.history.append({"role": role, "content": content})

    def history(self, thread_id: str) -> list[dict[str, str]]:
        return list(self.get_or_create(thread_id).history)
