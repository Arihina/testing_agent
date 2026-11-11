"""Вспомогательные функции."""


def _private_helper(x: int) -> int:
    return x * 2


def add(a: int, b: int) -> int:
    """Складывает два числа."""
    return a + b


def normalize(values: list[str]) -> list[str]:
    """Убирает пустые строки и приводит к нижнему регистру."""
    result = []
    for v in values:
        if v.strip():
            result.append(v.strip().lower())
    return result
