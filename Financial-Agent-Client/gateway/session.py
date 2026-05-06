"""Session management for Gateway requests — in-memory or SQLite-persisted."""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionState:
    thread_id: str
    history: list[dict[str, str]] = field(default_factory=list)


class SessionManager:
    """Session store keyed by thread id.

    When *db_path* is ``None`` (default) the store is purely in-memory and
    conversation history is lost on process restart.

    Pass a file path (e.g. ``"sessions.db"``) to enable SQLite persistence so
    history survives restarts and multi-session continuity becomes possible.
    Use ``":memory:"`` for an in-process SQLite instance useful in tests.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self._sessions: dict[str, SessionState] = {}
        self._conn: sqlite3.Connection | None = None
        if db_path is not None:
            self._conn = sqlite3.connect(db_path, check_same_thread=False)
            self._init_db()

    # ── DB lifecycle ────────────────────────────────────────────────────────

    def _init_db(self) -> None:
        assert self._conn is not None
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS session_messages (
                thread_id TEXT    NOT NULL,
                seq       INTEGER NOT NULL,
                role      TEXT    NOT NULL,
                content   TEXT    NOT NULL,
                PRIMARY KEY (thread_id, seq)
            )
            """
        )
        self._conn.commit()

    def _load_history(self, thread_id: str) -> list[dict[str, str]]:
        assert self._conn is not None
        rows = self._conn.execute(
            "SELECT role, content FROM session_messages WHERE thread_id = ? ORDER BY seq",
            (thread_id,),
        ).fetchall()
        return [{"role": role, "content": content} for role, content in rows]

    def _save_message(self, thread_id: str, seq: int, role: str, content: str) -> None:
        assert self._conn is not None
        self._conn.execute(
            "INSERT OR IGNORE INTO session_messages (thread_id, seq, role, content) VALUES (?, ?, ?, ?)",
            (thread_id, seq, role, content),
        )
        self._conn.commit()

    def close(self) -> None:
        """Close the SQLite connection (no-op in pure in-memory mode)."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "SessionManager":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ── Public API ──────────────────────────────────────────────────────────

    @staticmethod
    def new_thread_id(prefix: str = "thread") -> str:
        return f"{prefix}-{uuid.uuid4().hex[:8]}"

    def get_or_create(self, thread_id: str | None = None) -> SessionState:
        active_thread = thread_id or self.new_thread_id()
        if active_thread not in self._sessions:
            state = SessionState(thread_id=active_thread)
            if self._conn is not None:
                state.history = self._load_history(active_thread)
            self._sessions[active_thread] = state
        return self._sessions[active_thread]

    def append(self, thread_id: str, role: str, content: str) -> None:
        session = self.get_or_create(thread_id)
        session.history.append({"role": role, "content": content})
        if self._conn is not None:
            self._save_message(thread_id, len(session.history) - 1, role, content)

    def history(self, thread_id: str) -> list[dict[str, str]]:
        return list(self.get_or_create(thread_id).history)
