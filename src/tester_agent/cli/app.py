"""Приложение typer и регистрация подкоманд."""

import typer

app = typer.Typer(
    name="tester-agent",
    help="CLI-агент для автоматизации тестирования Python-бэкенда.",
    no_args_is_help=True,
)
