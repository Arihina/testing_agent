"""Test Synthesizer: ContextPackage → исходник тестового модуля."""

from __future__ import annotations

import re
from typing import Any

from ..contracts import ContextPackage
from .gateway import LLMGateway
from .prompts import PromptRegistry

_FENCE_RE = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL)


class TestSynthesizer:
    """Превращает ContextPackage в исходник pytest-модуля через LLM."""

    def __init__(
        self,
        gateway: LLMGateway,
        registry: PromptRegistry | None = None,
        artifact_store: Any | None = None,
    ) -> None:
        self.gateway = gateway
        self.registry = registry or PromptRegistry()
        self.artifact_store = artifact_store

    def synthesize(self, package: ContextPackage) -> str:
        """Возвращает исходник тестового модуля (без markdown-ограждений)."""
        system, user = self.registry.render(
            "test_generation", 1, context=self._render_context(package)
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        raw = self.gateway.complete(messages)
        if self.artifact_store is not None:
            self.artifact_store.save_prompt(messages, raw)
        return self._extract_code(raw)

    @staticmethod
    def _render_context(package: ContextPackage) -> str:
        lines = [
            f"Модуль: {package.module}",
            f"Функция: {package.name}",
            f"Сигнатура: {package.signature}",
        ]
        if package.docstring:
            lines.append(f"Докстринг: {package.docstring}")

        lines.append("")
        lines.append("Импорты модуля:")
        if package.imports:
            lines.extend(f"  {imp}" for imp in package.imports)
        else:
            lines.append("  (нет)")

        if package.called_functions:
            lines.append("")
            lines.append("Вызываемые функции (тот же модуль):")
            for fn in package.called_functions:
                lines.append(f"  {fn.signature}")
                lines.extend(f"    {ln}" for ln in fn.source.splitlines())

        if package.used_types:
            lines.append("")
            lines.append(f"Используемые типы: {', '.join(package.used_types)}")

        if package.type_definitions:
            lines.append("")
            lines.append("Определения типов:")
            for src in package.type_definitions:
                lines.extend(f"  {ln}" for ln in src.splitlines())

        if package.pydantic_models:
            lines.append("")
            lines.append("Pydantic-модели:")
            for src in package.pydantic_models:
                lines.extend(f"  {ln}" for ln in src.splitlines())

        if package.fixtures:
            lines.append("")
            lines.append("Доступные фикстуры:")
            lines.extend(f"  {fx}" for fx in package.fixtures)

        if package.test_style:
            lines.append("")
            lines.append("Стиль существующих тестов:")
            lines.extend(f"  {ln}" for ln in package.test_style.splitlines())

        return "\n".join(lines)

    @staticmethod
    def _extract_code(raw: str) -> str:
        match = _FENCE_RE.search(raw)
        if match:
            return match.group(1).strip()
        return raw.strip()
