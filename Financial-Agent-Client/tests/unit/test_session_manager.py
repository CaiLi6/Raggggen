"""Tests for gateway/session.py (task B3)."""

from __future__ import annotations

import pytest

from gateway.session import SessionManager, SessionState


def test_new_thread_id_has_prefix() -> None:
    tid = SessionManager.new_thread_id()
    assert tid.startswith("thread-")


def test_new_thread_id_custom_prefix() -> None:
    tid = SessionManager.new_thread_id(prefix="test")
    assert tid.startswith("test-")


def test_new_thread_id_is_unique() -> None:
    ids = {SessionManager.new_thread_id() for _ in range(20)}
    assert len(ids) == 20


def test_get_or_create_new_session() -> None:
    manager = SessionManager()
    session = manager.get_or_create("t1")
    assert isinstance(session, SessionState)
    assert session.thread_id == "t1"
    assert session.history == []


def test_get_or_create_returns_same_session() -> None:
    manager = SessionManager()
    s1 = manager.get_or_create("t1")
    s2 = manager.get_or_create("t1")
    assert s1 is s2


def test_get_or_create_auto_generates_thread_id() -> None:
    manager = SessionManager()
    session = manager.get_or_create(None)
    assert session.thread_id.startswith("thread-")


def test_append_adds_message_to_history() -> None:
    manager = SessionManager()
    manager.append("t1", "user", "hello")
    session = manager.get_or_create("t1")
    assert len(session.history) == 1
    assert session.history[0] == {"role": "user", "content": "hello"}


def test_append_multiple_messages() -> None:
    manager = SessionManager()
    manager.append("t1", "user", "q1")
    manager.append("t1", "assistant", "a1")
    manager.append("t1", "user", "q2")
    session = manager.get_or_create("t1")
    assert len(session.history) == 3
    assert session.history[1]["role"] == "assistant"


def test_history_returns_copy() -> None:
    manager = SessionManager()
    manager.append("t1", "user", "msg")
    h = manager.history("t1")
    h.append({"role": "user", "content": "extra"})
    session = manager.get_or_create("t1")
    assert len(session.history) == 1


def test_sessions_isolated() -> None:
    manager = SessionManager()
    manager.append("t1", "user", "msg-for-t1")
    session2 = manager.get_or_create("t2")
    assert session2.history == []


# ── SQLite persistence tests ─────────────────────────────────────────────────

def test_sqlite_memory_mode_basic() -> None:
    """':memory:' db_path gives a real SQLite session store."""
    sm = SessionManager(db_path=":memory:")
    sm.append("t1", "user", "hello")
    assert sm.history("t1") == [{"role": "user", "content": "hello"}]
    sm.close()


def test_persistence_survives_reload(tmp_path) -> None:
    """History written by one SessionManager is readable by a new one from same file."""
    db_file = str(tmp_path / "sessions.db")

    sm1 = SessionManager(db_path=db_file)
    sm1.append("thread-1", "user", "what is AAPL revenue?")
    sm1.append("thread-1", "assistant", "Apple Q3 revenue was $85B")
    sm1.close()

    sm2 = SessionManager(db_path=db_file)
    history = sm2.history("thread-1")
    sm2.close()

    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "what is AAPL revenue?"}
    assert history[1] == {"role": "assistant", "content": "Apple Q3 revenue was $85B"}


def test_persistence_order_preserved(tmp_path) -> None:
    """Messages are loaded in insertion order."""
    db_file = str(tmp_path / "sessions.db")

    sm1 = SessionManager(db_path=db_file)
    for i in range(5):
        sm1.append("t1", "user", f"message-{i}")
    sm1.close()

    sm2 = SessionManager(db_path=db_file)
    history = sm2.history("t1")
    sm2.close()

    assert [m["content"] for m in history] == [f"message-{i}" for i in range(5)]


def test_persistence_threads_isolated(tmp_path) -> None:
    """Different thread_ids in the same DB do not share history."""
    db_file = str(tmp_path / "sessions.db")

    sm1 = SessionManager(db_path=db_file)
    sm1.append("thread-A", "user", "message for A")
    sm1.append("thread-B", "user", "message for B")
    sm1.close()

    sm2 = SessionManager(db_path=db_file)
    assert len(sm2.history("thread-A")) == 1
    assert sm2.history("thread-A")[0]["content"] == "message for A"
    assert len(sm2.history("thread-B")) == 1
    sm2.close()


def test_persistence_context_manager(tmp_path) -> None:
    """SessionManager works as a context manager; closes cleanly on exit."""
    db_file = str(tmp_path / "sessions.db")

    with SessionManager(db_path=db_file) as sm:
        sm.append("t1", "user", "ctx msg")

    with SessionManager(db_path=db_file) as sm2:
        history = sm2.history("t1")

    assert history == [{"role": "user", "content": "ctx msg"}]


def test_in_memory_mode_no_conn(tmp_path, monkeypatch) -> None:
    """Default (db_path=None) never creates a SQLite connection."""
    sm = SessionManager()
    assert sm._conn is None
    sm.append("t1", "user", "hi")
    assert sm._conn is None  # still no conn after operations


def test_persistence_append_after_reload(tmp_path) -> None:
    """After reloading from DB, new appends are also persisted."""
    db_file = str(tmp_path / "sessions.db")

    with SessionManager(db_path=db_file) as sm1:
        sm1.append("t1", "user", "first")

    with SessionManager(db_path=db_file) as sm2:
        sm2.append("t1", "assistant", "second")

    with SessionManager(db_path=db_file) as sm3:
        history = sm3.history("t1")

    assert len(history) == 2
    assert history[0]["content"] == "first"
    assert history[1]["content"] == "second"
