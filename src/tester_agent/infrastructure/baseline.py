"""Baseline Store: метрики прошлых прогонов по машинам."""

from __future__ import annotations

import json
import platform
from pathlib import Path

from ..contracts import LoadMetrics


def machine_id() -> str:
    return platform.node() or "unknown"


class BaselineStore:
    """Хранит baseline.json: метрики по идентификатору машины."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(".testagent") / "baseline.json"
        self.data = self._load()

    def _load(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, mid: str) -> LoadMetrics | None:
        raw = self.data.get(mid)
        return LoadMetrics(**raw) if raw else None

    def set(self, metrics: LoadMetrics) -> None:
        self.data[metrics.machine_id] = metrics.model_dump()
        self._save()
