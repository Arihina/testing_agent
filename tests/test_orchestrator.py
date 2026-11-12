"""Тесты сценария unit (петля починки) на фейках."""

from pathlib import Path

from tester_agent.contracts import RunResult, Target
from tester_agent.orchestrator import UnitScenario


class _Ctx:
    target_source = "def f():\n    return 1\n"


class FakeBuilder:
    def build(self, target):
        return _Ctx()


class FakeSynthesizer:
    def __init__(self, sources):
        self.sources = list(sources)

    def synthesize(self, package):
        return self.sources.pop(0) if self.sources else "default"


class FakeRepairer:
    def __init__(self, sources):
        self.sources = list(sources)
        self.calls = 0

    def repair(self, source, output, target_source=""):
        self.calls += 1
        return self.sources.pop(0) if self.sources else source


class IdentityRepairer:
    def __init__(self):
        self.calls = 0

    def repair(self, source, output, target_source=""):
        self.calls += 1
        return source


class FakeAdapter:
    def __init__(self, results):
        self.results = list(results)

    def run(self, test_file, import_roots=None):
        return self.results.pop(0) if self.results else RunResult(passed=True, returncode=0, output="")


class FakeArtifacts:
    def write_test(self, name, code):
        return Path("/tmp") / f"test_{name}.py"


def _target():
    return Target(module="m", file_path="x.py", name="f", signature="def f()", line=1)


def test_repairs_until_pass():
    repairer = FakeRepairer(["fixed"])
    scenario = UnitScenario(
        builder=FakeBuilder(),
        synthesizer=FakeSynthesizer(["bad"]),
        repairer=repairer,
        adapter=FakeAdapter([
            RunResult(passed=False, returncode=1, output="fail"),
            RunResult(passed=True, returncode=0, output=""),
        ]),
        artifacts=FakeArtifacts(),
        max_repair_iterations=3,
    )
    candidate = scenario.run(_target())
    assert candidate.passed is True
    assert candidate.iteration == 1
    assert repairer.calls == 1
    assert candidate.source == "fixed"


def test_stops_after_limit():
    repairer = FakeRepairer(["v1", "v2", "v3", "v4"])
    scenario = UnitScenario(
        builder=FakeBuilder(),
        synthesizer=FakeSynthesizer(["bad"]),
        repairer=repairer,
        adapter=FakeAdapter([RunResult(passed=False, returncode=1, output="fail")] * 10),
        artifacts=FakeArtifacts(),
        max_repair_iterations=2,
    )
    candidate = scenario.run(_target())
    assert candidate.passed is False
    assert candidate.iteration == 2
    assert repairer.calls == 2


def test_stops_on_repeated_patch():
    repairer = IdentityRepairer()
    scenario = UnitScenario(
        builder=FakeBuilder(),
        synthesizer=FakeSynthesizer(["bad"]),
        repairer=repairer,
        adapter=FakeAdapter([RunResult(passed=False, returncode=1, output="fail")] * 10),
        artifacts=FakeArtifacts(),
        max_repair_iterations=5,
    )
    candidate = scenario.run(_target())
    assert candidate.passed is False
    assert candidate.iteration == 0
    assert repairer.calls == 1
