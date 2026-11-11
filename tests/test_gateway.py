"""Тесты LLM Gateway (с моками httpx)."""

import httpx
import pytest

from tester_agent.generation.gateway import LLMError, LLMGateway


def _response(content, status=200):
    request = httpx.Request("POST", "http://localhost")
    return httpx.Response(
        status,
        json={
            "choices": [{"message": {"content": content}}],
            "usage": {"total_tokens": 5},
        },
        request=request,
    )


def test_complete_returns_content(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _response("код теста"))
    gateway = LLMGateway()
    assert gateway.complete([{"role": "user", "content": "hi"}]) == "код теста"


def test_retries_then_succeeds(monkeypatch):
    calls = {"n": 0}

    def fake_post(*a, **k):
        calls["n"] += 1
        if calls["n"] < 3:
            return _response("", status=500)
        return _response("ok")

    monkeypatch.setattr(httpx, "post", fake_post)
    gateway = LLMGateway(max_retries=3)
    assert gateway.complete([{"role": "user", "content": "hi"}]) == "ok"
    assert calls["n"] == 3


def test_cache_avoids_repeat_calls(monkeypatch, tmp_path):
    calls = {"n": 0}

    def fake_post(*a, **k):
        calls["n"] += 1
        return _response("cached")

    monkeypatch.setattr(httpx, "post", fake_post)
    gateway = LLMGateway(cache_path=tmp_path / "cache.json")
    assert gateway.complete([{"role": "user", "content": "x"}]) == "cached"
    assert gateway.complete([{"role": "user", "content": "x"}]) == "cached"
    assert calls["n"] == 1


def test_raises_after_retries(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _response("", status=500))
    gateway = LLMGateway(max_retries=2)
    with pytest.raises(LLMError):
        gateway.complete([{"role": "user", "content": "x"}])
