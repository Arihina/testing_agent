"""Smoke Prober: по одному запросу на ручку, отсев не-2xx."""

from __future__ import annotations

import httpx

from ..contracts import RequestSpec


class SmokeProber:
    """Отсеивает ручки, не отвечающие 2xx."""

    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def probe(self, requests: list[RequestSpec]) -> list[RequestSpec]:
        passed: list[RequestSpec] = []
        for req in requests:
            try:
                resp = httpx.request(
                    req.method,
                    self.base_url + req.path,
                    params=req.query or None,
                    json=req.json_body,
                    timeout=self.timeout,
                )
                if 200 <= resp.status_code < 300:
                    passed.append(req)
            except httpx.HTTPError:
                continue
        return passed
