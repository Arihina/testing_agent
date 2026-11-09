"""Testing Agent — CLI-агент для автоматизации тестирования Python-бэкенда."""

__version__ = "0.1.0"


def main() -> None:
    """Точка входа консольной команды `tester-agent`."""
    from .cli import app

    app()
