"""Verdict Writer: метрики нагрузки + baseline → текстовая интерпретация."""

from __future__ import annotations

from typing import Any

from ..contracts import LoadMetrics
from .gateway import LLMGateway
from .prompts import PromptRegistry


class VerdictWriter:
    """Пишет справочную интерпретацию результатов нагрузки.

    Выход — только справочный текст, без quality gate (§1).
    """

    def __init__(
        self,
        gateway: LLMGateway,
        registry: PromptRegistry | None = None,
        artifact_store: Any | None = None,
    ) -> None:
        self.gateway = gateway
        self.registry = registry or PromptRegistry()
        self.artifact_store = artifact_store

    def write(self, metrics: LoadMetrics, baseline: LoadMetrics | None) -> str:
        system, user = self.registry.render(
            "load_verdict", 1,
            rps=metrics.rps,
            p50=metrics.latency_p50,
            p90=metrics.latency_p90,
            p99=metrics.latency_p99,
            error_rate=metrics.error_rate,
            baseline=self._render_baseline(baseline),
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        raw = self.gateway.complete(messages)
        if self.artifact_store is not None:
            self.artifact_store.save_prompt(messages, raw)
        return raw.strip()

    @staticmethod
    def _render_baseline(baseline: LoadMetrics | None) -> str:
        if baseline is None:
            return "(нет)"
        return (
            f"- RPS: {baseline.rps}\n"
            f"- p50: {baseline.latency_p50} ms\n"
            f"- p90: {baseline.latency_p90} ms\n"
            f"- p99: {baseline.latency_p99} ms\n"
            f"- доля ошибок: {baseline.error_rate}"
        )
