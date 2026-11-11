"""Команда `unit`: генерация и доводка unit-тестов."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from ...analysis import CandidateFilter, ContextBuilder, SourceScanner
from ...config.loader import load_config
from ..app import app
from ..exit_codes import EXIT_ENV_ERROR

console = Console()


@app.command("unit")
def unit(
    path: str | None = typer.Argument(
        None, help="Путь к пакету (иначе — из конфига targets)."),
    diff: bool = typer.Option(
        False, "--diff", help="Отбирать только объекты, изменённые относительно базовой ветки."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Показать отобранные цели и план без вызова модели."),
) -> None:
    """Сгенерировать и довести unit-тесты для функций и методов пакета."""
    config = load_config()
    scanner = SourceScanner()
    declarations = _collect_declarations(scanner, config, path, diff)
    targets = CandidateFilter().filter(
        declarations,
        coverage=None,
        known_hashes=_accepted_hashes(),
    )

    if dry_run:
        _print_targets(targets)
        if targets:
            builder = ContextBuilder()
            for target in targets:
                rprint(f"\n--- ContextPackage: {target.name} ---")
                rprint(builder.build(target).model_dump())
    else:
        typer.echo(f"Отобрано целей: {len(targets)}")
        typer.echo(
            "TODO (этапы 2–4): генерация и доводка тестов ещё не реализованы.")


def _collect_declarations(scanner, config, path, diff):
    if diff:
        return scanner.scan_git_diff(config.targets.base_branch)
    if path:
        return scanner.scan_package(path)
    if config.targets.include:
        declarations = []
        for p in config.targets.include:
            declarations.extend(scanner.scan_package(p))
        return declarations
    typer.echo(
        "Укажите путь к пакету или настройте targets.include в .testagent/config.toml.",
        err=True,
    )
    raise typer.Exit(EXIT_ENV_ERROR)


def _accepted_hashes() -> frozenset[str]:
    """Хеши сигнатур уже принятых тестов.

    Временная реализация: читает .testagent/state.json напрямую.
    Будет заменена на State Store (этап 4).
    """
    state_path = Path(".testagent") / "state.json"
    if not state_path.exists():
        return frozenset()
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return frozenset()
    return frozenset((data.get("accepted") or {}).keys())


def _print_targets(targets) -> None:
    typer.echo(f"Отобрано целей: {len(targets)}")
    table = Table(title="Цели для генерации тестов")
    table.add_column("name", no_wrap=True)
    table.add_column("complexity", justify="right")
    table.add_column("module")
    table.add_column("line", justify="right")
    for t in targets:
        table.add_row(t.name, str(t.complexity), t.module, str(t.line))
    console.print(table)
