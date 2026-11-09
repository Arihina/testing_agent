"""Команда `clean`: удалить артефакты прогонов."""

import typer

from ..app import app


@app.command("clean")
def clean() -> None:
    """Удалить артефакты прогонов, сохранив состояние."""
    typer.echo("TODO (этап 4): очистка .testagent/runs/.")
