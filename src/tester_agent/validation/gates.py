"""Quality gates: детерминированные проверки тестов."""

from __future__ import annotations

import ast


def syntax_ok(source: str) -> bool:
    """Syntax Gate: исходник компилируется."""
    try:
        compile(source, "<test>", "exec")
        return True
    except SyntaxError:
        return False


def assertion_violation(source: str, min_assert_ratio: float = 0.0) -> str | None:
    """Assertion Gate: возвращает причину отклонения или None.

    Эвристики («Тавтологии»): есть assert'ы, есть проверка конкретного
    значения, тест вызывает функцию, отношение assert'ов к строкам.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return "не компилируется"

    test_funcs = [
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
    ]
    if not test_funcs:
        return "нет тестовых функций"

    total_asserts = 0
    concrete = False
    has_call = False
    for fn in test_funcs:
        for node in ast.walk(fn):
            if isinstance(node, ast.Assert):
                total_asserts += 1
                if _is_concrete(node.test):
                    concrete = True
            if isinstance(node, ast.Call):
                has_call = True

    if total_asserts == 0:
        return "нет assert-проверок"
    if not has_call:
        return "тест не вызывает целевую функцию"
    if not concrete:
        return "нет проверки конкретного значения (только is/None)"
    if total_asserts / max(len(source.splitlines()), 1) < min_assert_ratio:
        return "слишком мало assert-ов"
    return None


def _is_concrete(node: ast.AST) -> bool:
    """Считается ли assert проверкой конкретного значения, а не тавтологией."""
    if isinstance(node, ast.Compare):
        ops = {type(op).__name__ for op in node.ops}
        return not ops <= {"Is", "IsNot"}
    return bool(isinstance(node, (ast.Call, ast.Constant)))


def coverage_covers_target(
    coverage: dict[str, set[int]],
    file_path: str,
    line: int,
    end_line: int | None,
) -> bool:
    """Coverage Gate: хотя бы одна строка целевой функции исполнена тестом."""
    covered = coverage.get(file_path, set())
    end = end_line or line
    return any(ln in covered for ln in range(line, end + 1))
