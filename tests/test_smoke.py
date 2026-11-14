"""Тесты Smoke Prober."""

import httpx

from tester_agent.contracts import RequestSpec
from tester_agent.execution import SmokeProber


class _Resp:
    def __init__(self, status):
        self.status_code = status


def test_probe_filters_non_2xx(monkeypatch):
    def fake_request(method, url, params=None, json=None, timeout=None):
        if "/ok" in url:
            return _Resp(200)
        return _Resp(404)

    monkeypatch.setattr(httpx, "request", fake_request)
    requests = [RequestSpec(method="GET", path="/ok"), RequestSpec(method="GET", path="/nope")]
    passed = SmokeProber("http://x").probe(requests)
    assert [r.path for r in passed] == ["/ok"]


def test_probe_swallows_errors(monkeypatch):
    def fake_request(*a, **k):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(httpx, "request", fake_request)
    requests = [RequestSpec(method="GET", path="/x")]
    assert SmokeProber("http://x").probe(requests) == []
