"""Sandbox Runner: запуск кода в отдельном процессе с жёстким таймаутом."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path


class RunOutput:
    """Сырой результат запуска команды."""

    def __init__(
        self,
        returncode: int,
        stdout: str,
        stderr: str,
        duration: float,
        timed_out: bool,
    ) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration
        self.timed_out = timed_out


class SandboxRunner:
    """Запускает команду в отдельном процессе с таймаутом.

    Сетевая изоляция пока не реализована — для полноценного отсечения сети
    потребуется контейнер или userns (TODO, §6).
    """

    def __init__(self, timeout_seconds: int = 60) -> None:
        self.timeout_seconds = timeout_seconds

    def run(
        self,
        command: list[str],
        cwd: str | Path | None = None,
        env: dict | None = None,
    ) -> RunOutput:
        start = time.monotonic()
        try:
            proc = subprocess.run(
                command,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
            return RunOutput(proc.returncode, proc.stdout, proc.stderr, time.monotonic() - start, False)
        except subprocess.TimeoutExpired as exc:
            return RunOutput(-1, self._text(exc.stdout), self._text(exc.stderr), time.monotonic() - start, True)
        except OSError as exc:
            return RunOutput(-1, "", str(exc), time.monotonic() - start, False)

    @staticmethod
    def _text(value) -> str:
        if value is None:
            return ""
        return value if isinstance(value, str) else value.decode("utf-8", "replace")
