"""Orchestrator: сценарий unit — генерация, прогон, починка и вердикт."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..analysis.paths import module_info
from ..contracts import Candidate, Target, Verdict


@dataclass
class UnitOutcome:
    name: str
    passed: bool
    iteration: int
    verdict: Verdict | None
    source: str = ""
    output: str = ""


class UnitScenario:
    """Реализует сценарий unit как конечный автомат (§3.2, §4)."""

    def __init__(
        self,
        builder,
        synthesizer,
        repairer,
        adapter,
        artifacts,
        validator,
        state_store,
        max_repair_iterations: int = 3,
    ) -> None:
        self.builder = builder
        self.synthesizer = synthesizer
        self.repairer = repairer
        self.adapter = adapter
        self.artifacts = artifacts
        self.validator = validator
        self.state_store = state_store
        self.max_repair_iterations = max_repair_iterations

    def run(self, target: Target) -> UnitOutcome:
        package = self.builder.build(target)
        source = self.synthesizer.synthesize(package)
        output = ""
        iteration = 0
        passed = False
        seen = {source}
        while True:
            test_file = self.artifacts.write_test(target.name, source)
            result = self.adapter.run(test_file, import_roots=[self._import_root(target)])
            output = result.output
            if result.passed:
                passed = True
                break
            if iteration >= self.max_repair_iterations:
                break
            repaired = self.repairer.repair(source, output, package.target_source)
            if repaired in seen:
                break
            seen.add(repaired)
            source = repaired
            iteration += 1

        candidate = Candidate(
            target=target, source=source, iteration=iteration, passed=passed, output=output
        )
        if not passed:
            verdict = Verdict(accepted=False, failed_gate="green", reason="тест не проходит")
        else:
            verdict = self.validator.validate(candidate, test_file, self._import_root(target))
            if verdict.accepted:
                self.state_store.accept(target)
                self.artifacts.save_accepted(target.name, source)
                self._write_to_tree(target, source)
            else:
                reason = verdict.reason or verdict.failed_gate or ""
                self.artifacts.save_rejected(target.name, source, reason)

        return UnitOutcome(
            name=target.name,
            passed=passed,
            iteration=iteration,
            verdict=verdict,
            source=source,
            output=output,
        )

    @staticmethod
    def _import_root(target: Target) -> Path:
        return module_info(target.file_path)[1]

    @staticmethod
    def _write_to_tree(target: Target, source: str) -> None:
        safe_name = target.name.replace(".", "_")
        test_path = Path(target.file_path).parent / f"test_{safe_name}.py"
        test_path.write_text(source, encoding="utf-8")
