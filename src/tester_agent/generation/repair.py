"""Repair Synthesizer: исходник + traceback → исправленный тест."""

from __future__ import annotations

from typing import Any

from .gateway import LLMGateway
from .prompts import PromptRegistry
from .synthesizer import extract_code


class RepairSynthesizer:
    """Чинит упавший тест по выводу pytest."""

    def __init__(
        self,
        gateway: LLMGateway,
        registry: PromptRegistry | None = None,
        artifact_store: Any | None = None,
    ) -> None:
        self.gateway = gateway
        self.registry = registry or PromptRegistry()
        self.artifact_store = artifact_store

    def repair(self, source: str, output: str, target_source: str = "") -> str:
        system, user = self.registry.render(
            "test_repair", 1, source=source, output=output, target_source=target_source
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        raw = self.gateway.complete(messages)
        if self.artifact_store is not None:
            self.artifact_store.save_prompt(messages, raw)
        code = extract_code(raw)
        return self._restore_imports(source, code)

    @staticmethod
    def _restore_imports(original: str, repaired: str) -> str:
        """Не даём починке потерять импорты исходного теста."""
        imports = [
            ln for ln in original.splitlines()
            if ln.strip().startswith(("import ", "from "))
        ]
        existing = {ln.strip() for ln in repaired.splitlines()}
        missing = [ln for ln in imports if ln.strip() not in existing]
        if not missing:
            return repaired
        return "\n".join(missing) + "\n\n" + repaired
