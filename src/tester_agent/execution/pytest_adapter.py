"""Pytest Adapter: прогон сгенерированного теста."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from ..contracts import RunResult
from .coverage import parse_coverage_xml
from .sandbox import SandboxRunner


class PytestAdapter:
    """Запускает pytest для одного тестового файла и возвращает RunResult."""

    def __init__(self, sandbox: SandboxRunner | None = None) -> None:
        self.sandbox = sandbox or SandboxRunner()

    def run(self, test_file: Path, import_roots: list[Path] | None = None) -> RunResult:
        command = [
            sys.executable, "-m", "pytest", str(test_file),
            "-q", "--no-header", "-p", "no:cacheprovider",
        ]
        out = self.sandbox.run(command, env=self._env(import_roots))
        return RunResult(
            passed=out.returncode == 0,
            returncode=out.returncode,
            output=out.stdout + out.stderr,
            duration=out.duration,
        )

    def run_coverage(
        self,
        test_file: Path,
        module: str,
        import_roots: list[Path] | None = None,
        cov_xml: Path | None = None,
    ) -> dict[str, set[int]]:
        """Прогоняет тест под coverage и возвращает {file_path: {покрытые строки}}."""
        cov_xml = cov_xml or (test_file.parent / "coverage.xml")
        command = [
            sys.executable, "-m", "pytest", str(test_file),
            "-q", "--no-header", "-p", "no:cacheprovider",
            f"--cov={module}", f"--cov-report=xml:{cov_xml}",
        ]
        self.sandbox.run(command, env=self._env(import_roots))
        if not cov_xml.exists():
            return {}
        return parse_coverage_xml(cov_xml)

    @staticmethod
    def _env(import_roots: list[Path] | None) -> dict:
        env = os.environ.copy()
        if import_roots:
            extra = os.pathsep.join(str(r) for r in import_roots)
            existing = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = extra if not existing else extra + os.pathsep + existing
        return env
