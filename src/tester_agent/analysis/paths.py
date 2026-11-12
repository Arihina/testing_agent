"""Определение dotted-пути модуля и корня импорта по пути файла."""

from __future__ import annotations

from pathlib import Path


def module_info(path: str | Path) -> tuple[str, Path]:
    """Возвращает ``(dotted-путь модуля, корень импорта)``.

    Поднимаемся по пакетам (директориям с ``__init__.py``), пока не упрёмся
    в директорию без ``__init__.py`` — она и есть корень для ``sys.path``.
    """
    p = Path(path)
    parts: list[str] = []
    current = p.parent
    while (current / "__init__.py").exists():
        parts.append(current.name)
        current = current.parent
    import_root = current
    parts.reverse()
    if p.stem != "__init__":
        parts.append(p.stem)
    return ".".join(parts), import_root
