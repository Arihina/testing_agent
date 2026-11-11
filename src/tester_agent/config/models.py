"""Модели конфигурации (pydantic) — источник значений по умолчанию."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TargetsConfig(BaseModel):
    """Раздел `targets`: пути и режим отбора целей."""

    include: list[str] = Field(default_factory=list, description="Пути/пакеты для включения.")
    exclude: list[str] = Field(default_factory=list, description="Пути/пакеты для исключения.")
    mode: Literal["package", "diff"] = "package"
    base_branch: str = "main"


class GenerationConfig(BaseModel):
    """Раздел `generation`: параметры LLM-генерации (локальная Ollama)."""

    model: str = "qwen2.5-coder:14b"
    base_url: str = "http://localhost:11434/v1"  # OpenAI-совместимый endpoint Ollama
    temperature: float = 0.2
    max_repair_iterations: int = 3
    token_budget: int = 200_000
    timeout_seconds: int = 120
    max_retries: int = 3


class GatesConfig(BaseModel):
    """Раздел `gates`: пороги валидации (Validation)."""

    min_coverage_delta: float = 0.0
    assertion_enabled: bool = True
    min_assert_ratio: float = 0.05
    coverage_enabled: bool = True
    isolation_enabled: bool = True


class ExecutionConfig(BaseModel):
    """Раздел `execution`: изоляция и таймауты."""

    timeout_seconds: int = 60
    isolation: Literal["subprocess", "container"] = "subprocess"
    environment_path: str | None = None
    network_enabled: bool = False


class LoadConfig(BaseModel):
    """Раздел `load`: параметры нагрузочного прогона."""

    base_url: str = "http://localhost:8000"
    tool: Literal["wrk2", "k6"] = "k6"
    warmup_seconds: int = 10
    duration_seconds: int = 30
    rate: int = 50
    regression_threshold: float = 0.2


class OutputConfig(BaseModel):
    """Раздел `output`: детализация отчёта."""

    verbosity: Literal["quiet", "normal", "verbose"] = "normal"
    format: Literal["json", "markdown", "both"] = "both"


class Config(BaseModel):
    """Корневая конфигурация агента."""

    targets: TargetsConfig = Field(default_factory=TargetsConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    gates: GatesConfig = Field(default_factory=GatesConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    load: LoadConfig = Field(default_factory=LoadConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
