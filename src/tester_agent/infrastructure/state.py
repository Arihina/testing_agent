"""State Store: хеши сигнатур принятых тестов, идемпотентность."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from ..contracts import Target


class StateStore:
    """Хранит состояние прогонов в state.json."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(".testagent") / "state.json"
        self.data = self._load()

    def _load(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def accepted_hashes(self) -> frozenset[str]:
        return frozenset(self.data.get("accepted", {}).keys())

    def is_accepted(self, signature_hash: str) -> bool:
        return signature_hash in self.data.get("accepted", {})

    def accept(self, target: Target) -> None:
        self.data.setdefault("accepted", {})[target.signature_hash] = {
            "name": target.name,
            "module": target.module,
            "signature": target.signature,
            "accepted_at": datetime.now(UTC).isoformat(),
        }
        self._save()
