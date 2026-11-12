"""Pytest Adapter: прогон сгенерированного теста."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from ..contracts import RunResult
from .sandbox import SandboxRunner


class PytestAdapter:
    """Запускает pytest для одного тестового файла и возвращает RunResult."""

    def __init__(self, sandbox: SandboxRunner | None = None) -> None:
        self.sandbox = sandbox or SandboxRunner()

    def run(self, test_file: Path, import_roots: list[Path] | None = None) -> RunResult:
        env = os.environ.copy()
        if import_roots:
            extra = os.pathsep.join(str(r) for r in import_roots)
            existing = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = extra if not existing else extra + \
                os.pathsep + existing

        command = [
            sys.executable,
            "-m",
            "pytest",
            str(test_file),
            "-q",
            "--no-header",
            "-p",
            "no:cacheprovider",
        ]
        out = self.sandbox.run(command, env=env)
        output = out.stdout + out.stderr
        return RunResult(
            passed=out.returncode == 0,
            returncode=out.returncode,
            output=output,
            duration=out.duration,
        )
