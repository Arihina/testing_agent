"""CLI Layer: разбор команд, конфиг, вывод отчёта (§3.2)."""

from . import commands  # noqa: F401  — импорт регистрирует подкоманды
from .app import app

__all__ = ["app"]
