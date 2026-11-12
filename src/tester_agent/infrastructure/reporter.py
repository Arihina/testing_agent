"""Reporter: сводка прогона в файлы report.json / report.md."""

from __future__ import annotations

import json
from pathlib import Path


class Reporter:
    """Пишет машинночитаемый и человекочитаемый отчёты в директорию прогона."""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir

    def write_report(self, outcomes: list) -> None:
        rows = [self._row(o) for o in outcomes]
        (self.run_dir / "report.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (self.run_dir / "report.md").write_text(self._markdown(rows), encoding="utf-8")

    @staticmethod
    def _row(o) -> dict:
        verdict = o.verdict
        return {
            "name": o.name,
            "passed": o.passed,
            "iteration": o.iteration,
            "accepted": bool(verdict and verdict.accepted),
            "failed_gate": verdict.failed_gate if verdict else None,
            "reason": verdict.reason if verdict else None,
        }

    @staticmethod
    def _markdown(rows: list[dict]) -> str:
        lines = [
            "# Отчёт прогона unit",
            "",
            "| Цель | Итерации | Green | Вердикт |",
            "|---|---|---|---|",
        ]
        for r in rows:
            green = "PASS" if r["passed"] else "FAIL"
            if r["accepted"]:
                verdict = "✅ accepted"
            else:
                verdict = f"❌ rejected ({r['failed_gate']}: {r['reason']})"
            lines.append(f"| {r['name']} | {r['iteration']} | {green} | {verdict} |")
        return "\n".join(lines) + "\n"
