"""Тесты State Store."""

from tester_agent.contracts import Target
from tester_agent.infrastructure import StateStore


def test_accept_and_hashes(tmp_path):
    store = StateStore(tmp_path / "state.json")
    target = Target(
        module="m", file_path="x.py", name="f", signature="def f()",
        line=1, signature_hash="abc123",
    )
    assert store.is_accepted("abc123") is False
    store.accept(target)
    assert store.is_accepted("abc123") is True
    assert store.accepted_hashes() == frozenset({"abc123"})


def test_loads_existing(tmp_path):
    path = tmp_path / "state.json"
    path.write_text('{"accepted": {"h1": {"name": "f"}}}', encoding="utf-8")
    store = StateStore(path)
    assert store.is_accepted("h1") is True
