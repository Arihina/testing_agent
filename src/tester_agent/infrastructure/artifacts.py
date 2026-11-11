"""Artifact Store: директория прогона runs/<timestamp>/ (§7)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class ArtifactStore:
    """Создаёт runs/<timestamp>/ и сохраняет промпты, ответы и сгенерированный код."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(".testagent")
        self.run_dir: Path | None = None
        self._prompt_index = 0

    def create_run(self) -> Path:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.run_dir = self.root / "runs" / stamp
        (self.run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        (self.run_dir / "generated").mkdir(parents=True, exist_ok=True)
        self._prompt_index = 0
        return self.run_dir

    def save_prompt(self, messages: list[dict[str, str]], response: str) -> None:
        if self.run_dir is None:
            self.create_run()
        self._prompt_index += 1
        prompt_dir = self.run_dir / "prompts"
        (prompt_dir / f"{self._prompt_index:03d}_messages.json").write_text(
            json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (prompt_dir / f"{self._prompt_index:03d}_response.txt").write_text(response, encoding="utf-8")

    def save_generated(self, name: str, code: str) -> None:
        if self.run_dir is None:
            self.create_run()
        safe_name = name.replace(".", "_")
        (self.run_dir / "generated" / f"{safe_name}.py").write_text(code, encoding="utf-8")
