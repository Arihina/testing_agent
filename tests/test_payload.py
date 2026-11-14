"""Тесты Payload Synthesizer."""

from tester_agent.contracts import Endpoint, EndpointParam
from tester_agent.generation import PayloadSynthesizer


def test_path_param_substitution():
    endpoint = Endpoint(
        method="GET",
        path="/users/{id}",
        parameters=[EndpointParam(name="id", location="path", required=True, param_schema={"type": "integer"})],
    )
    req = PayloadSynthesizer().synthesize(endpoint)
    assert req.path == "/users/1"
    assert req.json_body is None


def test_body_from_ref():
    schemas = {
        "User": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "email": {"type": "string", "format": "email"},
            },
        }
    }
    endpoint = Endpoint(
        method="POST", path="/users",
        request_body_schema={"$ref": "#/components/schemas/User"},
    )
    req = PayloadSynthesizer(schemas).synthesize(endpoint)
    assert req.json_body == {"id": 1, "email": "user@example.com"}


def test_query_params():
    endpoint = Endpoint(
        method="GET", path="/users",
        parameters=[EndpointParam(name="limit", location="query", param_schema={"type": "integer"})],
    )
    req = PayloadSynthesizer().synthesize(endpoint)
    assert req.query == {"limit": 1}
