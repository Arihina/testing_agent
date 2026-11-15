"""Тесты Verdict Writer."""

from tester_agent.contracts import LoadMetrics
from tester_agent.generation import VerdictWriter


class FakeGateway:
    def __init__(self, response):
        self._response = response
        self.messages = None

    def complete(self, messages):
        self.messages = messages
        return self._response


def test_write_returns_text():
    gw = FakeGateway("p99 вырос — вероятно, узкое место в БД")
    text = VerdictWriter(gw).write(LoadMetrics(rps=10, latency_p99=2.0), None)
    assert text == "p99 вырос — вероятно, узкое место в БД"


def test_prompt_contains_metrics():
    gw = FakeGateway("ok")
    metrics = LoadMetrics(rps=10, latency_p99=2.0)
    baseline = LoadMetrics(rps=8, latency_p99=1.0)
    VerdictWriter(gw).write(metrics, baseline)
    user = gw.messages[1]["content"]
    assert "10" in user
    assert "2.0" in user
    assert "1.0" in user
