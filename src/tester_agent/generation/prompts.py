"""Prompt Registry: версионированные шаблоны промптов, отделённые от логики."""

from __future__ import annotations

TEST_GENERATION_SYSTEM = """\
Ты — ассистент по написанию unit-тестов на Python (pytest).

Сгенерируй ОДИН тестовый модуль для указанной функции или метода.
Жёсткие правила:
- Отвечай только кодом pytest, без пояснений и без markdown-ограждений.
- Используй переданный контекст: сигнатуру, докстринг, типы, импорты, фикстуры.
- Импортируй целевую функцию/класс и все используемые типы по путям модулей из контекста.
- Тест должен реально вызывать функцию с конкретными входными данными.
- Проверяй конкретные значения и поведение, а не только `is not None`.
- Не пиши тесты на приватные функции и методы.
- Следуй стилю существующих тестов, если он передан.
"""

TEST_GENERATION_USER = """\
Сгенерируй pytest-тест для следующей цели.

{context}
"""

REPAIR_SYSTEM = """\
Ты — ассистент по починке упавших unit-тестов (pytest).
Исправь тест так, чтобы он проходил, сохраняя его смысл.
Жёсткие правила:
- Отвечай только исправленным кодом pytest, без пояснений и markdown-ограждений.
- СОХРАНИ все импорты из текущего тестового модуля без изменений.
- Исправляй фактические ошибки: импорты, вызовы, ожидаемые значения.
- Не удаляй проверки без необходимости; если ожидаемое значение неверно — вычисли его заново по коду целевой функции.
"""

REPAIR_USER = """\
Тест упал. Исправь его.

Целевая функция:
{target_source}

Текущий тестовый модуль:
{source}

Вывод pytest (traceback):
{output}
"""

_REGISTRY: dict[tuple[str, int], tuple[str, str]] = {
    ("test_generation", 1): (TEST_GENERATION_SYSTEM, TEST_GENERATION_USER),
    ("test_repair", 1): (REPAIR_SYSTEM, REPAIR_USER),
}


class PromptRegistry:
    """Хранит версионированные шаблоны и рендерит их в (system, user)."""

    def render(self, name: str, version: int, **context: str) -> tuple[str, str]:
        key = (name, version)
        if key not in _REGISTRY:
            raise KeyError(f"Неизвестный промпт: {name} v{version}")
        system, user_template = _REGISTRY[key]
        return system, user_template.format(**context)
