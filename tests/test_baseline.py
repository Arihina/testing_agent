"""Тесты Baseline Store."""

from tester_agent.contracts import LoadMetrics
from tester_agent.infrastructure import BaselineStore


def test_set_and_get(tmp_path):
    store = BaselineStore(tmp_path / "baseline.json")
    metrics = LoadMetrics(rps=10.0, latency_p99=2.0, machine_id="m1")
    assert store.get("m1") is None
    store.set(metrics)
    got = store.get("m1")
    assert got is not None
    assert got.latency_p99 == 2.0
