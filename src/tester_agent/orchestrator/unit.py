"""Orchestrator: сценарий unit — генерация, прогон и петля починки."""

from __future__ import annotations

from pathlib import Path

from ..analysis.paths import module_info
from ..contracts import Candidate, Target


class UnitScenario:
    """Реализует сценарий unit как конечный автомат (§3.2, §4).

    Для каждой цели: контекст → генерация → прогон pytest → при падении
    починка по traceback, максимум ``max_repair_iterations`` итераций.
    """

    def __init__(
        self,
        builder,
        synthesizer,
        repairer,
        adapter,
        artifacts,
        max_repair_iterations: int = 3,
    ) -> None:
        self.builder = builder
        self.synthesizer = synthesizer
        self.repairer = repairer
        self.adapter = adapter
        self.artifacts = artifacts
        self.max_repair_iterations = max_repair_iterations

    def run(self, target: Target) -> Candidate:
        package = self.builder.build(target)
        source = self.synthesizer.synthesize(package)
        output = ""
        iteration = 0
        passed = False
        seen = {source}
        while True:
            test_file = self.artifacts.write_test(target.name, source)
            result = self.adapter.run(test_file, import_roots=[
                                      self._import_root(target)])
            output = result.output
            if result.passed:
                passed = True
                break
            if iteration >= self.max_repair_iterations:
                break
            repaired = self.repairer.repair(
                source, output, package.target_source)
            if repaired in seen:
                break  # патч повторяется — петля не сходится, не тратим бюджет
            seen.add(repaired)
            source = repaired
            iteration += 1
        return Candidate(
            target=target,
            source=source,
            iteration=iteration,
            passed=passed,
            output=output,
        )

    @staticmethod
    def _import_root(target: Target) -> Path:
        return module_info(target.file_path)[1]
