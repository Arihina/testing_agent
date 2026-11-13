"""Regression Gate: метрики нагрузки не деградировали относительно baseline."""

from __future__ import annotations

from ..contracts import LoadMetrics, Verdict


def check_regression(current: LoadMetrics, baseline: LoadMetrics | None, threshold: float) -> Verdict:
    if baseline is None or baseline.latency_p99 <= 0:
        return Verdict(accepted=True)
    delta = (current.latency_p99 - baseline.latency_p99) / baseline.latency_p99
    if delta > threshold:
        return Verdict(accepted=False, failed_gate="regression", reason=f"p99 вырос на {delta:.0%}")
    return Verdict(accepted=True)
