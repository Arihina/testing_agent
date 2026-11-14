"""Payload Synthesizer: JSON-схема → тела запросов и параметры."""

from __future__ import annotations

from ..contracts import Endpoint, RequestSpec


class PayloadSynthesizer:
    """Синтезирует правдоподобные тела и параметры по OpenAPI-схеме."""

    def __init__(self, schemas: dict | None = None) -> None:
        self.schemas = schemas or {}

    def synthesize(self, endpoint: Endpoint) -> RequestSpec:
        path = endpoint.path
        query: dict = {}
        for param in endpoint.parameters:
            value = self._value_for(param.param_schema or {}, param.name)
            if param.location == "path":
                path = path.replace("{" + param.name + "}", str(value))
            elif param.location == "query":
                query[param.name] = value
        body = None
        if endpoint.request_body_schema:
            body = self._value_for(endpoint.request_body_schema, "body")
        return RequestSpec(method=endpoint.method, path=path, query=query, json_body=body)

    def _value_for(self, schema: dict, name: str):
        schema = self._resolve(schema)
        type_ = schema.get("type")
        if type_ == "string":
            return self._string_value(schema, name)
        if type_ in ("integer", "number"):
            return 1
        if type_ == "boolean":
            return True
        if type_ == "array":
            item_schema = schema.get("items") or {}
            return [self._value_for(item_schema, name)]
        if type_ == "object":
            props = schema.get("properties") or {}
            return {k: self._value_for(v, k) for k, v in props.items()}
        return None

    def _resolve(self, schema: dict) -> dict:
        ref = schema.get("$ref")
        if not ref or not ref.startswith("#/"):
            return schema
        name = ref.split("/")[-1]
        return self.schemas.get(name, schema)

    @staticmethod
    def _string_value(schema: dict, name: str) -> str:
        fmt = schema.get("format")
        if fmt == "email":
            return "user@example.com"
        if fmt == "uuid":
            return "00000000-0000-0000-0000-000000000000"
        if fmt in ("date-time", "date"):
            return "2024-01-01T00:00:00Z"
        if name in ("id", "user_id"):
            return "1"
        if name == "name":
            return "example"
        enum = schema.get("enum")
        if enum:
            return str(enum[0])
        return "example"
