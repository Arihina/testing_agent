"""Тесты Repair Synthesizer."""

from tester_agent.generation.repair import RepairSynthesizer


class FakeGateway:
    def __init__(self, response):
        self._response = response
        self.messages = None

    def complete(self, messages):
        self.messages = messages
        return self._response


def test_repair_extracts_code():
    gw = FakeGateway("```python\ndef test_fixed():\n    assert True\n```")
    code = RepairSynthesizer(gw).repair("bad", "traceback")
    assert "def test_fixed()" in code
    assert "```" not in code


def test_repair_prompt_contains_source_and_output():
    gw = FakeGateway("ok")
    RepairSynthesizer(gw).repair("SRC", "OUT")
    user = gw.messages[1]["content"]
    assert "SRC" in user
    assert "OUT" in user


def test_repair_restores_dropped_imports():
    gw = FakeGateway("def test_x():\n    assert True\n")
    original = "import pytest\nfrom sample_pkg.utils import normalize\n\ndef test_x():\n    assert True\n"
    code = RepairSynthesizer(gw).repair(original, "traceback")
    assert "import pytest" in code
    assert "from sample_pkg.utils import normalize" in code
