"""Validator: выносит вердикт по цепочке quality gates."""

from __future__ import annotations

from pathlib import Path

from ..config.models import GatesConfig
from ..contracts import Candidate, Verdict
from . import gates


class Validator:
    """Единственный, кто выносит вердикт о принятии теста."""

    def __init__(self, adapter, gates_config: GatesConfig) -> None:
        self.adapter = adapter
        self.gates_config = gates_config

    def validate(self, candidate: Candidate, test_file: Path, import_root: Path) -> Verdict:
        target = candidate.target

        if not gates.syntax_ok(candidate.source):
            return Verdict(accepted=False, failed_gate="syntax", reason="тест не компилируется")
        if not candidate.passed:
            return Verdict(accepted=False, failed_gate="green", reason="тест не проходит")

        if self.gates_config.coverage_enabled:
            coverage = self.adapter.run_coverage(test_file, target.module, [import_root])
            if not gates.coverage_covers_target(
                coverage, target.file_path, target.line, target.end_line
            ):
                return Verdict(
                    accepted=False,
                    failed_gate="coverage",
                    reason="тест не покрывает целевую функцию",
                )

        if self.gates_config.assertion_enabled:
            violation = gates.assertion_violation(
                candidate.source, self.gates_config.min_assert_ratio
            )
            if violation:
                return Verdict(accepted=False, failed_gate="assertion", reason=violation)

        if self.gates_config.isolation_enabled:
            second = self.adapter.run(test_file, import_roots=[import_root])
            if not second.passed:
                return Verdict(
                    accepted=False,
                    failed_gate="isolation",
                    reason="тест нестабилен (повторный прогон упал)",
                )

        return Verdict(accepted=True)
