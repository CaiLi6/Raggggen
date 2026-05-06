"""Tests for gateway/session.py (task B3)."""

from __future__ import annotations

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
