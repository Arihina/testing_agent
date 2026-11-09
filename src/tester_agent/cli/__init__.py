"""CLI Layer: разбор команд, конфиг, вывод отчёта"""

from .app import app
from . import commands  # noqa: F401  — импорт регистрирует подкоманды

__all__ = ["app"]
