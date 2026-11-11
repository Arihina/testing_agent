"""Spec Reader: чтение OpenAPI-спецификации → список Endpoint."""

from __future__ import annotations

import json
from pathlib import Path

import httpx

from ..contracts import Endpoint, EndpointParam

_HTTP_METHODS = {"get", "post", "put", "patch",
                 "delete", "head", "options", "trace"}


class SpecReader:
    """Нормализует OpenAPI 3.x в список эндпоинтов."""

    def read(self, source: str | Path) -> list[Endpoint]:
        """Читает спецификацию из файла (Path/строка пути) или URL."""
        if isinstance(source, str) and source.startswith(("http://", "https://")):
            resp = httpx.get(source, follow_redirects=True, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
        else:
            data = json.loads(Path(source).read_text(encoding="utf-8"))
        return self.parse(data)

    def parse(self, data: dict) -> list[Endpoint]:
        endpoints: list[Endpoint] = []
        global_security = data.get("security")
        for path, path_item in (data.get("paths") or {}).items():
            common_params = path_item.get("parameters") or []
            for method, operation in path_item.items():
                if method not in _HTTP_METHODS or not isinstance(operation, dict):
                    continue
                endpoint = Endpoint(
                    method=method.upper(),
                    path=path,
                    summary=operation.get("summary"),
                )
                endpoint.parameters = [
                    self._param(p) for p in list(common_params) + list(operation.get("parameters") or [])
                ]
                body = operation.get("requestBody") or {}
                app_json = (body.get("content") or {}).get(
                    "application/json") or {}
                endpoint.request_body_schema = app_json.get("schema")
                endpoint.responses = self._responses(operation)
                endpoint.requires_auth = bool(
                    operation.get("security") or global_security)
                endpoints.append(endpoint)
        return endpoints

    @staticmethod
    def _param(p: dict) -> EndpointParam:
        required = p.get("required", False)
        if p.get("in") == "path":
            required = True
        return EndpointParam(
            name=p.get("name", ""),
            location=p.get("in", "query"),
            required=bool(required),
            param_schema=p.get("schema"),
        )

    @staticmethod
    def _responses(operation: dict) -> dict[str, dict | None]:
        result: dict[str, dict | None] = {}
        for status, response in (operation.get("responses") or {}).items():
            app_json = ((response or {}).get("content")
                        or {}).get("application/json") or {}
            result[status] = app_json.get("schema")
        return result
