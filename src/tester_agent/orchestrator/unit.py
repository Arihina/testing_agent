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
    """Реализует сценарий unit как конечный автомат."""

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
        tests_dir: str | None = None,
    ) -> None:
        self.builder = builder
        self.synthesizer = synthesizer
        self.repairer = repairer
        self.adapter = adapter
        self.artifacts = artifacts
        self.validator = validator
        self.state_store = state_store
        self.max_repair_iterations = max_repair_iterations
        self.tests_dir = tests_dir

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

    def _write_to_tree(self, target: Target, source: str) -> None:
        safe_name = target.name.replace(".", "_")
        target_dir = Path(self.tests_dir) if self.tests_dir else Path(target.file_path).parent
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / f"test_{safe_name}.py").write_text(source, encoding="utf-8")
