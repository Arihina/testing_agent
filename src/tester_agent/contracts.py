"""Контракты между слоями: структуры данных, а не прямые вызовы."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Target(BaseModel):
    """Объект тестирования: функция или метод, отобранный Analysis-слоем."""

    module: str  # dotted-путь модуля, напр. "sample_pkg.service"
    file_path: str  # путь к файлу
    name: str  # квалифицированное имя, напр. "UserService.find_by_name"
    signature: str  # человекочитаемая сигнатура
    docstring: str | None = None
    line: int  # первая строка
    end_line: int | None = None  # последняя строка (если известна)
    complexity: int = 1  # цикломатическая сложность
    is_method: bool = False
    is_async: bool = False
    signature_hash: str = ""  # хеш сигнатуры для идемпотентности
    covered: bool | None = None  # True / False / None (неизвестно)


class FunctionSnippet(BaseModel):
    """Фрагмент вызываемой функции для контекста (глубина 1)."""

    name: str
    signature: str
    source: str


class ContextPackage(BaseModel):
    """Пакет контекста, уходящий в промпт (§3.3)."""

    module: str
    name: str
    signature: str
    docstring: str | None = None
    imports: list[str] = Field(default_factory=list)
    called_functions: list[FunctionSnippet] = Field(default_factory=list)
    used_types: list[str] = Field(default_factory=list)
    type_definitions: list[str] = Field(default_factory=list)
    pydantic_models: list[str] = Field(default_factory=list)
    fixtures: list[str] = Field(default_factory=list)
    test_style: str | None = None


class EndpointParam(BaseModel):
    """Параметр эндпоинта из OpenAPI."""

    name: str
    location: str  # path | query | header | cookie
    required: bool = False
    param_schema: dict | None = None


class Endpoint(BaseModel):
    """Нормализованная ручка OpenAPI (§3.3)."""

    method: str
    path: str
    summary: str | None = None
    parameters: list[EndpointParam] = Field(default_factory=list)
    request_body_schema: dict | None = None
    responses: dict[str, dict | None] = Field(default_factory=dict)
    requires_auth: bool = False
