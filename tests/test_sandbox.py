"""Тесты Sandbox Runner."""

import sys

from tester_agent.execution.sandbox import SandboxRunner


def test_runs_and_captures():
    out = SandboxRunner().run([sys.executable, "-c", "print('hi')"])
    assert out.returncode == 0
    assert "hi" in out.stdout


def test_timeout():
    runner = SandboxRunner(timeout_seconds=1)
    out = runner.run([sys.executable, "-c", "import time; time.sleep(5)"])
    assert out.timed_out is True
    assert out.returncode == -1
