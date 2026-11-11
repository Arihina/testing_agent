"""Source Scanner: обход AST, сбор объявлений функций и методов."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from ..contracts import Target
from .astutil import (
    cyclomatic_complexity,
    function_signature,
    iter_functions,
    signature_hash,
)

_SKIP_PARTS = {"__pycache__", ".venv", "venv", ".git", "site-packages"}


class SourceScanner:
    """Собирает объявления функций/методов из Python-файлов."""

    def scan_package(self, path: str | Path) -> list[Target]:
        """Сканировать все Python-файлы пакета (рекурсивно)."""
        root = Path(path)
        return self._scan_files(self._python_files(root), root)

    def scan_files(self, files: list[str | Path]) -> list[Target]:
        """Сканировать явно переданные файлы (без привязки к корню пакета)."""
        return self._scan_files([Path(f) for f in files], None)

    def scan_git_diff(self, base_branch: str) -> list[Target]:
        """Сканировать Python-файлы, изменённые относительно базовой ветки."""
        cmd = ["git", "diff", "--name-only", "--diff-filter=ACMR", base_branch]
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if proc.returncode != 0:
            return []
        files = [line for line in proc.stdout.splitlines()
                 if line.endswith(".py")]
        return self.scan_files(files)

    def _python_files(self, root: Path) -> list[Path]:
        if root.is_file():
            return [root] if root.suffix == ".py" else []
        files: list[Path] = []
        for p in sorted(root.rglob("*.py")):
            if _SKIP_PARTS.intersection(p.parts):
                continue
            if p.name.startswith("test_") or p.name.endswith("_test.py"):
                continue
            files.append(p)
        return files

    def _scan_files(self, files: list[Path], root: Path | None) -> list[Target]:
        targets: list[Target] = []
        for path in files:
            if not path.exists():
                continue
            try:
                source = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            try:
                tree = ast.parse(source, filename=str(path))
            except SyntaxError:
                continue
            module = self._module_name(path, root)
            for func, class_name in iter_functions(tree):
                targets.append(self._to_target(
                    func, class_name, module, str(path)))
        return targets

    def _module_name(self, path: Path, root: Path | None) -> str:
        if root is not None and root.is_dir():
            rel = path.relative_to(root)
        else:
            rel = Path(path.name)
        parts = list(rel.with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts)

    def _to_target(self, func, class_name: str | None, module: str, file_path: str) -> Target:
        name = f"{class_name}.{func.name}" if class_name else func.name
        signature = function_signature(func)
        return Target(
            module=module,
            file_path=file_path,
            name=name,
            signature=signature,
            docstring=ast.get_docstring(func),
            line=func.lineno,
            end_line=getattr(func, "end_lineno", None),
            complexity=cyclomatic_complexity(func),
            is_method=class_name is not None,
            is_async=isinstance(func, ast.AsyncFunctionDef),
            signature_hash=signature_hash(module, name, signature),
        )
