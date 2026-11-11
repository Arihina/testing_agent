"""LLM Gateway: единая точка вызова модели (локальная Ollama)."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import httpx


class LLMError(RuntimeError):
    """Ошибка вызова модели."""


class LLMGateway:
    """Вызывает Ollama через OpenAI-совместимый endpoint.

    Отвечает за ретраи, таймауты, учёт токенов и кеш по хешу промпта (§3.2).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model: str = "qwen2.5-coder:14b",
        temperature: float = 0.2,
        timeout_seconds: int = 120,
        max_retries: int = 3,
        token_budget: int = 200_000,
        cache_path: Path | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.token_budget = token_budget
        self.tokens_used = 0
        self.cache_path = cache_path
        self._cache: dict[str, dict[str, Any]] = {}
        if cache_path is not None:
            self._cache = self._load_cache()

    # публичный API

    def complete(self, messages: list[dict[str, str]], *, use_cache: bool = True) -> str:
        """Возвращает текст ответа модели для списка сообщений."""
        key = self._prompt_hash(messages)
        if use_cache and key in self._cache:
            return self._cache[key]["response"]
        response = self._call_with_retries(messages)
        if use_cache and self.cache_path is not None:
            self._cache[key] = {"messages": messages, "response": response}
            self._save_cache()
        return response

    # вызов модели

    def _call_with_retries(self, messages: list[dict[str, str]]) -> str:
        if self.tokens_used >= self.token_budget:
            raise LLMError(f"Бюджет токенов исчерпан: {self.tokens_used} >= {self.token_budget}")
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": False,
        }
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                resp = httpx.post(url, json=payload, timeout=self.timeout_seconds)
                if resp.status_code >= 500:
                    raise LLMError(f"Ошибка сервера Ollama: {resp.status_code}")
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                self._account_tokens(data.get("usage"))
                return content
            except (httpx.HTTPError, KeyError, ValueError, LLMError) as exc:
                last_error = exc
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
        raise LLMError(f"Вызов модели не удался после {self.max_retries} попыток: {last_error}")

    def _account_tokens(self, usage: dict | None) -> None:
        if not usage:
            return
        total = usage.get("total_tokens")
        if total is None:
            total = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
        self.tokens_used += int(total)

    # кеш

    def _prompt_hash(self, messages: list[dict[str, str]]) -> str:
        payload = json.dumps({"model": self.model, "messages": messages}, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _load_cache(self) -> dict[str, dict[str, Any]]:
        try:
            return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save_cache(self) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(
                json.dumps(self._cache, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass
