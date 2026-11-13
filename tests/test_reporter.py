"""Тесты Reporter."""

from tester_agent.contracts import Verdict
from tester_agent.infrastructure import Reporter
from tester_agent.orchestrator import UnitOutcome


def test_write_report(tmp_path):
    outcomes = [
        UnitOutcome(name="f", passed=True, iteration=0, verdict=Verdict(accepted=True)),
        UnitOutcome(
            name="g", passed=False, iteration=2,
            verdict=Verdict(accepted=False, failed_gate="green", reason="тест не проходит"),
        ),
    ]
    Reporter(tmp_path).write_report(outcomes)

    report_json = (tmp_path / "report.json").read_text(encoding="utf-8")
    report_md = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert '"accepted": true' in report_json
    assert "✅ accepted" in report_md
    assert "green" in report_md
