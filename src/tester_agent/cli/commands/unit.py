"""Команда `unit`: генерация и доводка unit-тестов."""

import typer
from rich import print as rprint

from ...config.loader import load_config
from ..app import app


@app.command("unit")
def unit(
    path: str | None = typer.Argument(None, help="Путь к пакету (иначе — из конфига targets)."),
    diff: bool = typer.Option(False, "--diff", help="Отбирать только объекты, изменённые относительно базовой ветки."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Показать отобранные цели и план без вызова модели."),
) -> None:
    """Сгенерировать и довести unit-тесты для функций и методов пакета."""
    config = load_config()
    if dry_run:
        rprint("Резолв конфигурации:")
        rprint(config.model_dump())
        typer.echo("\nTODO (этап 1): Source Scanner и Candidate Filter — список целей появится здесь.")
    else:
        typer.echo("TODO (этапы 2–4): генерация и доводка тестов ещё не реализованы.")
    if path:
        typer.echo(f"Явная цель: {path}")
    if diff:
        typer.echo("Режим: только diff относительно базовой ветки.")
