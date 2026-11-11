"""Тесты Test Synthesizer (с фейковым gateway)."""

from tester_agent.contracts import ContextPackage
from tester_agent.generation.synthesizer import TestSynthesizer as Synthesizer


class FakeGateway:
    def __init__(self, response):
        self._response = response
        self.messages = None

    def complete(self, messages):
        self.messages = messages
        return self._response


def _pkg():
    return ContextPackage(module="svc", name="f", signature="def f(x: int) -> int", docstring="Делает")


def test_extracts_code_from_fence():
    gw = FakeGateway("```python\ndef test_x():\n    pass\n```")
    code = Synthesizer(gw).synthesize(_pkg())
    assert "def test_x()" in code
    assert "```" not in code


def test_no_fence_returns_raw():
    raw = "def test_x():\n    assert True\n"
    gw = FakeGateway(raw)
    assert Synthesizer(gw).synthesize(_pkg()) == raw.strip()


def test_prompt_contains_context():
    gw = FakeGateway("ok")
    Synthesizer(gw).synthesize(_pkg())
    assert gw.messages[0]["role"] == "system"
    user = gw.messages[1]["content"]
    assert "svc" in user
    assert "def f(x: int) -> int" in user
    assert "Делает" in user
