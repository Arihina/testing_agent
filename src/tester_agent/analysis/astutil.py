"""Вспомогательные функции для работы с AST: обход, сложность, сигнатуры, хеш."""

from __future__ import annotations

import ast
import hashlib


def iter_functions(tree: ast.Module):
    """Yield (функция/метод, имя класса или None).

    Учитываются функции верхнего уровня и методы классов (глубина 1).
    Вложенные функции и классы внутри функций не рассматриваются.
    """
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node, None
        elif isinstance(node, ast.ClassDef):
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    yield member, node.name


def function_signature(func: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Человекочитаемая сигнатура функции из AST."""
    prefix = "async def" if isinstance(func, ast.AsyncFunctionDef) else "def"
    args = ast.unparse(func.args)
    ret = f" -> {ast.unparse(func.returns)}" if func.returns is not None else ""
    return f"{prefix} {func.name}({args}){ret}"


def signature_hash(module: str, name: str, signature: str) -> str:
    """Стабильный хеш сигнатуры цели (для идемпотентности, §4)."""
    payload = f"{module}.{name} :: {signature}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class _ComplexityVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.value = 1

    def _inc(self, n: int = 1) -> None:
        self.value += n

    def visit_If(self, node: ast.If) -> None:
        self._inc()
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self._inc()
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self._inc()
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._inc()
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self._inc()
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self._inc()
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self._inc(len(node.values) - 1)
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        self._inc(len(node.ifs))
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:
        self._inc(len(node.cases))
        self.generic_visit(node)


def cyclomatic_complexity(node: ast.AST) -> int:
    """Цикломатическая сложность (McCabe) узла функции."""
    visitor = _ComplexityVisitor()
    visitor.visit(node)
    return visitor.value
