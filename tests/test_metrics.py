"""Тесты Load Script Builder и Metrics Parser."""

from tester_agent.contracts import RequestSpec
from tester_agent.execution import LoadScriptBuilder, MetricsParser


def test_load_script_builds_valid_js():
    requests = [
        RequestSpec(method="GET", path="/users"),
        RequestSpec(method="POST", path="/users", json_body={"id": 1}),
    ]
    script = LoadScriptBuilder().build("http://h", requests, rate=10, warmup=1, duration=2)
    assert "import http from 'k6/http';" in script
    assert "http.get('http://h/users');" in script
    assert "http.post" in script
    assert "JSON.stringify" in script
    assert "target: 10" in script
    assert "{{" not in script  # нет необработанных фигурных скобок


def test_metrics_parser():
    summary = {
        "metrics": {
            "http_reqs": {"values": {"rate": 100.5}},
            "http_req_duration": {"values": {"avg": 2.0, "p(50)": 1.5, "p(90)": 3.0, "p(99)": 4.0}},
            "http_req_failed": {"values": {"rate": 0.01}},
        }
    }
    metrics = MetricsParser().parse(summary, machine_id="m1")
    assert metrics.rps == 100.5
    assert metrics.latency_p50 == 1.5
    assert metrics.latency_p99 == 4.0
    assert metrics.error_rate == 0.01
    assert metrics.machine_id == "m1"
