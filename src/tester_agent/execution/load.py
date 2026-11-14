"""Load Script Builder, Load Runner и Metrics Parser."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..contracts import LoadMetrics, RequestSpec

_K6_TEMPLATE = """\
import http from 'k6/http';
import {{ sleep }} from 'k6';

export const options = {{
  stages: [
    {{ duration: '{warmup}s', target: {rate} }},
    {{ duration: '{duration}s', target: {rate} }},
  ],
}};

export default function () {{
{requests}
  sleep(1);
}}
"""


class LoadScriptBuilder:
    """Собирает k6-скрипт из шаблона и payload'ов (без свободной генерации)."""

    def build(
        self,
        base_url: str,
        requests: list[RequestSpec],
        rate: int,
        warmup: int,
        duration: int,
    ) -> str:
        lines = [self._request_line(req, base_url) for req in requests]
        return _K6_TEMPLATE.format(
            warmup=warmup, duration=duration, rate=rate, requests="\n".join(lines),
        )

    @staticmethod
    def _request_line(req: RequestSpec, base_url: str) -> str:
        url = base_url + req.path
        method = req.method.lower()
        if req.json_body is not None:
            body = json.dumps(req.json_body)
            return (
                f"  http.{method}({url!r}, JSON.stringify({body}), "
                "{ headers: { 'Content-Type': 'application/json' } });"
            )
        return f"  http.{method}({url!r});"


class LoadRunner:
    """Запускает k6 и возвращает распарсенные метрики."""

    def __init__(self, k6_bin: str | None = None) -> None:
        self.k6_bin = k6_bin or shutil.which("k6")

    def run(self, script: str, summary_export: Path) -> LoadMetrics:
        if not self.k6_bin:
            raise RuntimeError("k6 не найден — установите его (см. §5)")
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
            fh.write(script)
            script_path = fh.name
        command = [self.k6_bin, "run", "--summary-export", str(summary_export), script_path]
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"k6 завершился с кодом {proc.returncode}: {proc.stderr}")
        summary = json.loads(summary_export.read_text(encoding="utf-8"))
        return MetricsParser().parse(summary)


class MetricsParser:
    """Разбирает k6 summary-export в LoadMetrics (§5)."""

    def parse(self, summary: dict, machine_id: str = "") -> LoadMetrics:
        metrics = summary.get("metrics", {})
        reqs = metrics.get("http_reqs", {}).get("values", {})
        dur = metrics.get("http_req_duration", {}).get("values", {})
        failed = metrics.get("http_req_failed", {}).get("values", {})
        avg = float(dur.get("avg", 0.0))
        return LoadMetrics(
            rps=float(reqs.get("rate", 0.0)),
            latency_p50=float(dur.get("p(50)") or dur.get("med") or avg),
            latency_p90=float(dur.get("p(90)") or avg),
            latency_p99=float(dur.get("p(99)") or avg),
            error_rate=float(failed.get("rate", 0.0)),
            machine_id=machine_id,
        )
