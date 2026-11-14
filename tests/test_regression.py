"""Тесты Regression Gate."""

from tester_agent.contracts import LoadMetrics
from tester_agent.validation import check_regression


def test_no_baseline_ok():
    assert check_regression(LoadMetrics(latency_p99=2.0), None, 0.2).accepted is True


def test_regression_detected():
    baseline = LoadMetrics(latency_p99=1.0)
    current = LoadMetrics(latency_p99=1.5)
    verdict = check_regression(current, baseline, 0.2)
    assert verdict.accepted is False
    assert verdict.failed_gate == "regression"


def test_no_regression():
    baseline = LoadMetrics(latency_p99=1.0)
    current = LoadMetrics(latency_p99=1.1)
    assert check_regression(current, baseline, 0.2).accepted is True
