"""Context Builder: формирование ContextPackage для промпта"""

from __future__ import annotations

import ast
from pathlib import Path

from ..contracts import ContextPackage, FunctionSnippet, Target
from .astutil import function_signature

_PYDANTIC_BASES = {"BaseModel", "BaseSettings", "RootModel"}
_BUILTIN_NAMES = {
    "int", "str", "float", "bool", "bytes", "list", "dict", "set", "tuple",
    "frozenset", "None", "Optional", "Any", "Union", "Literal", "Iterable",
    "Sequence", "Mapping", "Callable", "Awaitable", "TypeVar", "Generic",
    "Self", "Annotated",
}


class ContextBuilder:
    """Собирает контекст цели: вызываемые функции, типы, фикстуры, стиль тестов."""

    def build(self, target: Target) -> ContextPackage:
        path = Path(target.file_path)
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        func = self._find_function(tree, target.name)
        class_name = target.name.split(".")[0] if target.is_method else None

        used_types = self._used_types(func)
        type_defs, pydantic = self._type_sources(
            tree, path, used_types, source)

        return ContextPackage(
            module=target.module,
            name=target.name,
            signature=target.signature,
            docstring=target.docstring,
            target_source=ast.get_source_segment(source, func) or "",
            imports=self._collect_imports(tree),
            called_functions=self._called_functions(
                tree, func, class_name, source),
            used_types=sorted(used_types),
            type_definitions=type_defs,
            pydantic_models=pydantic,
            fixtures=self._fixtures(path),
            test_style=self._test_style(path),
        )

    # поиск объявлений

    @staticmethod
    def _find_function(tree: ast.Module, name: str):
        parts = name.split(".")
        if len(parts) == 1:
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == parts[0]:
                    return node
        elif len(parts) == 2:
            for node in tree.body:
                if isinstance(node, ast.ClassDef) and node.name == parts[0]:
                    for member in node.body:
                        if (
                            isinstance(
                                member, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and member.name == parts[1]
                        ):
                            return member
        raise ValueError(f"Не найдено объявление {name!r}")

    @staticmethod
    def _collect_imports(tree: ast.Module) -> list[str]:
        return [
            ast.unparse(node)
            for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]

    # вызываемые функции

    def _called_functions(self, tree, func, class_name, source) -> list[FunctionSnippet]:
        defined = self._defined_functions(tree)
        class_methods = self._class_method_map(tree)
        found: dict[str, FunctionSnippet] = {}
        for stmt in func.body:
            for node in ast.walk(stmt):
                if not isinstance(node, ast.Call):
                    continue
                target_name, target_node = None, None
                if isinstance(node.func, ast.Name):
                    target_name = node.func.id
                    target_node = defined.get(target_name)
                elif isinstance(node.func, ast.Attribute):
                    base = node.func.value
                    if isinstance(base, ast.Name) and base.id in ("self", "cls") and class_name:
                        target_name = node.func.attr
                        target_node = class_methods.get(
                            class_name, {}).get(target_name)
                if target_node is not None and target_name not in found:
                    found[target_name] = FunctionSnippet(
                        name=target_name,
                        signature=function_signature(target_node),
                        source=ast.get_source_segment(
                            source, target_node) or "",
                    )
        return list(found.values())

    @staticmethod
    def _defined_functions(tree: ast.Module) -> dict[str, ast.AST]:
        return {
            n.name: n
            for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

    @staticmethod
    def _class_method_map(tree: ast.Module) -> dict[str, dict[str, ast.AST]]:
        result: dict[str, dict[str, ast.AST]] = {}
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                result[node.name] = {
                    m.name: m
                    for m in node.body
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                }
        return result

    # типы и модели

    @staticmethod
    def _used_types(func) -> set[str]:
        names: set[str] = set()
        for annotation in ContextBuilder._annotations(func):
            for node in ast.walk(annotation):
                if isinstance(node, ast.Name) and node.id not in _BUILTIN_NAMES:
                    names.add(node.id)
        return names

    @staticmethod
    def _annotations(func) -> list[ast.AST]:
        args = func.args
        result: list[ast.AST] = []
        for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs):
            if arg.annotation is not None:
                result.append(arg.annotation)
        if args.vararg and args.vararg.annotation is not None:
            result.append(args.vararg.annotation)
        if args.kwarg and args.kwarg.annotation is not None:
            result.append(args.kwarg.annotation)
        if func.returns is not None:
            result.append(func.returns)
        return result

    def _type_sources(self, tree, path, used_types, source):
        imported = self._imported_modules(tree, path)
        type_defs: list[str] = []
        pydantic: list[str] = []
        seen: set[str] = set()
        for name in used_types:
            if name in seen:
                continue
            for mod_tree, mod_source in [(tree, source), *imported]:
                found = self._find_type(mod_tree, mod_source, name)
                if found is not None:
                    src, is_pydantic = found
                    seen.add(name)
                    (pydantic if is_pydantic else type_defs).append(src)
                    break
        return type_defs, pydantic

    def _imported_modules(self, tree, path):
        result: list[tuple[ast.Module, str]] = []
        seen: set[Path] = set()
        for mod_path in self._import_map(tree, path).values():
            if mod_path in seen or not mod_path.exists():
                continue
            seen.add(mod_path)
            try:
                mod_source = mod_path.read_text(encoding="utf-8")
                result.append(
                    (ast.parse(mod_source, filename=str(mod_path)), mod_source))
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue
        return result

    @staticmethod
    def _import_map(tree, path) -> dict[str, Path]:
        """Сопоставляет импортированные имена их файлам (эвристика для плоских пакетов)."""
        base = path.parent
        mapping: dict[str, Path] = {}
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                target_dir = base
                for _ in range(max(node.level - 1, 0)):
                    target_dir = target_dir.parent
                parts = node.module.split(".") if node.module else []
                target_file = target_dir.joinpath(*parts).with_suffix(".py")
                if not parts:
                    target_file = target_dir / "__init__.py"
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    mapping[alias.asname or alias.name] = target_file
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    mapping[alias.asname or alias.name] = base / \
                        (alias.name.split(".")[0] + ".py")
        return mapping

    @staticmethod
    def _find_type(tree, source, name):
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == name:
                return (
                    ast.get_source_segment(source, node) or "",
                    ContextBuilder._is_pydantic(node),
                )
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
                return (ast.get_source_segment(source, node) or "", False)
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Subscript):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == name:
                        return (ast.get_source_segment(source, node) or "", False)
        return None

    @staticmethod
    def _is_pydantic(node: ast.ClassDef) -> bool:
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in _PYDANTIC_BASES:
                return True
            if isinstance(base, ast.Attribute) and base.attr in _PYDANTIC_BASES:
                return True
        return False

    # фикстуры и стиль тестов

    def _fixtures(self, path: Path) -> list[str]:
        conftest = self._find_conftest(path)
        if conftest is None:
            return []
        source = conftest.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(conftest))
        return [
            function_signature(node)
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and self._has_fixture_decorator(node)
        ]

    @staticmethod
    def _find_conftest(path: Path) -> Path | None:
        for parent in (path.parent, *path.parent.parents):
            candidate = parent / "conftest.py"
            if candidate.exists():
                return candidate
        return None

    @staticmethod
    def _has_fixture_decorator(node) -> bool:
        for decorator in node.decorator_list:
            target = decorator.func if isinstance(
                decorator, ast.Call) else decorator
            if isinstance(target, ast.Name) and target.id == "fixture":
                return True
            if isinstance(target, ast.Attribute) and target.attr == "fixture":
                return True
        return False

    def _test_style(self, path: Path) -> str | None:
        candidates = list(path.parent.glob("test_*.py"))
        for parent in path.parent.parents:
            tests_dir = parent / "tests"
            if tests_dir.is_dir():
                candidates.extend(tests_dir.glob("test_*.py"))
        if not candidates:
            return None
        source = candidates[0].read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(candidates[0]))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                return ast.get_source_segment(source, node)
        return None
