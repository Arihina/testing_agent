"""Команда `report`: сводка последнего прогона."""

import typer

from ..app import app


@app.command("report")
def report() -> None:
    """Вывести сводку последнего прогона."""
    typer.echo("TODO (этап 4): Reporter.")
