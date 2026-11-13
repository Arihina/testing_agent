"""Тесты quality gates."""

from tester_agent.validation.gates import (
    assertion_violation,
    coverage_covers_target,
    syntax_ok,
)


def test_syntax_ok():
    assert syntax_ok("def test_x():\n    assert True\n") is True
    assert syntax_ok("def test_x(:\n") is False


def test_assertion_violation_tautology():
    src = "def test_x():\n    result = f(1)\n    assert result is not None\n"
    violation = assertion_violation(src)
    assert violation is not None
    assert "конкретного" in violation


def test_assertion_violation_ok():
    src = "def test_x():\n    result = f(1, 2)\n    assert result == 3\n"
    assert assertion_violation(src) is None


def test_assertion_violation_no_asserts():
    src = "def test_x():\n    f(1)\n"
    assert assertion_violation(src) == "нет assert-проверок"


def test_coverage_covers_target():
    coverage = {"/x/service.py": {10, 11, 12}}
    assert coverage_covers_target(coverage, "/x/service.py", 5, 11) is True
    assert coverage_covers_target(coverage, "/x/service.py", 20, 25) is False
