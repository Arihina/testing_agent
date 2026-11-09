"""Команда `load`: построить профиль и прогнать нагрузку."""

import typer

from ..app import app


@app.command("load")
def load(
    base_url: str | None = typer.Argument(None, help="Базовый URL сервиса (иначе — config.load.base_url)."),
    baseline: bool = typer.Option(False, "--baseline", help="Зафиксировать текущие метрики как эталон."),
) -> None:
    """Построить нагрузочный профиль из /openapi.json и прогнать нагрузку."""
    typer.echo(f"load: base_url={base_url}, baseline={baseline}")
    typer.echo("TODO (этап 5): Spec Reader, Smoke Prober, Load Runner.")
