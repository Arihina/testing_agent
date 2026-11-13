"""Тесты сценария unit (петля починки + вердикт) на фейках."""

from pathlib import Path

from tester_agent.contracts import RunResult, Target, Verdict
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
    def __init__(self, root):
        self.root = root

    def write_test(self, name, code):
        return self.root / f"test_{name}.py"

    def save_accepted(self, name, code):
        pass

    def save_rejected(self, name, code, reason):
        pass


class FakeValidator:
    def __init__(self, accepted=True):
        self.accepted = accepted

    def validate(self, candidate, test_file, import_root):
        if self.accepted:
            return Verdict(accepted=True)
        return Verdict(accepted=False, failed_gate="assertion", reason="тест")


class FakeStateStore:
    def __init__(self):
        self.accepted = []

    def accept(self, target):
        self.accepted.append(target)


def _scenario(**overrides):
    kwargs = {
        "builder": FakeBuilder(),
        "synthesizer": FakeSynthesizer(["bad"]),
        "repairer": FakeRepairer(["fixed"]),
        "adapter": FakeAdapter([
            RunResult(passed=False, returncode=1, output="fail"),
            RunResult(passed=True, returncode=0, output=""),
        ]),
        "artifacts": FakeArtifacts(Path("/tmp")),
        "validator": FakeValidator(accepted=True),
        "state_store": FakeStateStore(),
        "max_repair_iterations": 3,
    }
    kwargs.update(overrides)
    return UnitScenario(**kwargs)


def _target(file_path="x.py"):
    return Target(module="m", file_path=file_path, name="f", signature="def f()", line=1)


def test_repairs_until_pass_and_accepts(tmp_path):
    state = FakeStateStore()
    repairer = FakeRepairer(["fixed"])
    scenario = _scenario(
        repairer=repairer,
        artifacts=FakeArtifacts(tmp_path),
        state_store=state,
    )
    outcome = scenario.run(_target(str(tmp_path / "mod.py")))
    assert outcome.passed is True
    assert outcome.iteration == 1
    assert outcome.verdict.accepted is True
    assert outcome.source == "fixed"
    assert repairer.calls == 1
    assert len(state.accepted) == 1
    assert (tmp_path / "test_f.py").exists()


def test_stops_after_limit():
    repairer = FakeRepairer(["v1", "v2", "v3", "v4"])
    scenario = _scenario(
        repairer=repairer,
        adapter=FakeAdapter([RunResult(passed=False, returncode=1, output="fail")] * 10),
        max_repair_iterations=2,
    )
    outcome = scenario.run(_target())
    assert outcome.passed is False
    assert outcome.iteration == 2
    assert outcome.verdict.failed_gate == "green"


def test_stops_on_repeated_patch():
    repairer = IdentityRepairer()
    scenario = _scenario(
        repairer=repairer,
        adapter=FakeAdapter([RunResult(passed=False, returncode=1, output="fail")] * 10),
        max_repair_iterations=5,
    )
    outcome = scenario.run(_target())
    assert outcome.passed is False
    assert outcome.iteration == 0
    assert repairer.calls == 1
