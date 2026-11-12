"""Тесты Pytest Adapter (реальный прогон pytest на временных файлах)."""

from tester_agent.execution.pytest_adapter import PytestAdapter


def test_passing(tmp_path):
    test_file = tmp_path / "test_ok.py"
    test_file.write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    result = PytestAdapter().run(test_file)
    assert result.passed is True


def test_failing(tmp_path):
    test_file = tmp_path / "test_bad.py"
    test_file.write_text("def test_bad():\n    assert 1 == 2\n", encoding="utf-8")
    result = PytestAdapter().run(test_file)
    assert result.passed is False
    assert "assert 1 == 2" in result.output
