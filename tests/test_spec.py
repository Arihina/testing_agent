"""Тесты Spec Reader."""

from pathlib import Path

from tester_agent.analysis.spec import SpecReader

FIXTURE = Path(__file__).parent / "fixtures" / "openapi.json"


def test_read_endpoints():
    endpoints = SpecReader().read(FIXTURE)
    keys = {(e.method, e.path) for e in endpoints}
    assert ("GET", "/users") in keys
    assert ("POST", "/users") in keys
    assert ("GET", "/users/{id}") in keys
    assert len(endpoints) == 3


def test_path_param_required():
    endpoint = next(e for e in SpecReader().read(FIXTURE) if e.path == "/users/{id}")
    assert endpoint.parameters[0].name == "id"
    assert endpoint.parameters[0].required is True


def test_auth_and_body():
    endpoints = SpecReader().read(FIXTURE)
    post = next(e for e in endpoints if e.method == "POST")
    assert post.requires_auth is True
    assert post.request_body_schema["$ref"] == "#/components/schemas/User"

    get = next(e for e in endpoints if e.method == "GET")
    assert get.requires_auth is False
