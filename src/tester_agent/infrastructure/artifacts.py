"""Artifact Store: директория прогона runs/<timestamp>/."""

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
        (prompt_dir /
         f"{self._prompt_index:03d}_response.txt").write_text(response, encoding="utf-8")

    def write_test(self, name: str, code: str) -> Path:
        """Записывает выполняемый тестовый файл (test_<name>.py) и возвращает путь."""
        if self.run_dir is None:
            self.create_run()
        safe_name = name.replace(".", "_")
        test_file = self.run_dir / "generated" / f"test_{safe_name}.py"
        test_file.write_text(code, encoding="utf-8")
        return test_file

    def save_generated(self, name: str, code: str) -> None:
        """Сохраняет итоговый исходник теста для справки."""
        if self.run_dir is None:
            self.create_run()
        safe_name = name.replace(".", "_")
        (self.run_dir / "generated" /
         f"{safe_name}.py").write_text(code, encoding="utf-8")

    def save_accepted(self, name: str, code: str) -> Path:
        """Сохраняет принятый тест в runs/<ts>/accepted/."""
        return self._save_into("accepted", name, code)

    def save_rejected(self, name: str, code: str, reason: str) -> Path:
        """Сохраняет отклонённый тест и причину в runs/<ts>/rejected/."""
        path = self._save_into("rejected", name, code)
        path.with_suffix(".reason.txt").write_text(reason, encoding="utf-8")
        return path

    def _save_into(self, subdir: str, name: str, code: str) -> Path:
        if self.run_dir is None:
            self.create_run()
        safe_name = name.replace(".", "_")
        target_dir = self.run_dir / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / f"{safe_name}.py"
        path.write_text(code, encoding="utf-8")
        return path
