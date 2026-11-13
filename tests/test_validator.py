"""Тесты Validator (с фейковым adapter)."""

from pathlib import Path

from tester_agent.config.models import GatesConfig
from tester_agent.contracts import Candidate, RunResult, Target
from tester_agent.validation import Validator


class FakeAdapter:
    def __init__(self, coverage, second_passed=True):
        self.coverage = coverage
        self.second_passed = second_passed

    def run_coverage(self, test_file, module, import_roots=None):
        return self.coverage

    def run(self, test_file, import_roots=None):
        return RunResult(passed=self.second_passed, returncode=0, output="")


def _candidate(source="def test_x():\n    assert f(1) == 2\n", passed=True):
    target = Target(
        module="m", file_path="/x/service.py", name="f",
        signature="def f()", line=1, end_line=3,
    )
    return Candidate(target=target, source=source, passed=passed)


def _validator(coverage, **gate_kwargs):
    return Validator(FakeAdapter(coverage), GatesConfig(**gate_kwargs))


def test_accepts_all_gates():
    verdict = _validator({"/x/service.py": {1, 2, 3}}).validate(
        _candidate(), Path("/tmp/test_f.py"), Path("/")
    )
    assert verdict.accepted is True


def test_rejects_on_coverage():
    verdict = _validator({}).validate(_candidate(), Path("/tmp/test_f.py"), Path("/"))
    assert verdict.accepted is False
    assert verdict.failed_gate == "coverage"


def test_rejects_on_assertion():
    src = "def test_x():\n    r = f(1)\n    assert r is not None\n"
    verdict = _validator({"/x/service.py": {1, 2, 3}}).validate(
        _candidate(src), Path("/tmp/test_f.py"), Path("/")
    )
    assert verdict.accepted is False
    assert verdict.failed_gate == "assertion"
