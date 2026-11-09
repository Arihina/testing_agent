"""Слияние конфигурации: дефолты → config.toml → env → флаги."""

from __future__ import annotations

import json
import os
import tomllib
from pathlib import Path
from typing import Any

from .models import Config

ENV_PREFIX = "TESTER_AGENT_"
DEFAULT_CONFIG_PATH = Path(".testagent") / "config.toml"


def load_config(
    path: Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> Config:
    """Собрать конфигурацию из всех источников по возрастанию приоритета.

    Порядок: значения по умолчанию → файл config.toml → переменные окружения
    → флаги CLI (передаются как ``overrides``).
    """
    data: dict[str, Any] = Config().model_dump()

    config_path = path or DEFAULT_CONFIG_PATH
    if config_path.exists():
        file_data = tomllib.loads(config_path.read_text(encoding="utf-8"))
        _deep_merge(data, file_data)

    _deep_merge(data, _read_env())

    if overrides:
        _deep_merge(data, overrides)

    return Config.model_validate(data)


def _read_env() -> dict[str, Any]:
    """Переменные окружения ``TESTER_AGENT_*``, вложенность через ``__``.

    Пример: ``TESTER_AGENT_GENERATION__MAX_REPAIR_ITERATIONS=5``.
    """
    result: dict[str, Any] = {}
    for key, value in os.environ.items():
        if not key.startswith(ENV_PREFIX):
            continue
        rest = key[len(ENV_PREFIX):].lower()
        if not rest:
            continue
        _set_nested(result, rest.split("__"), _coerce(value))
    return result


def _coerce(value: str) -> Any:
    """Строку env → число/булево/список (JSON), иначе оставить строкой."""
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return value


def _set_nested(target: dict[str, Any], keys: list[str], value: Any) -> None:
    for key in keys[:-1]:
        target = target.setdefault(key, {})
    target[keys[-1]] = value


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    """Рекурсивно наложить ``override`` поверх ``base`` (in-place)."""
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
