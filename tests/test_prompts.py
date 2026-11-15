"""Тесты Prompt Registry."""

import pytest

from tester_agent.generation.prompts import PromptRegistry


def test_render_known_prompt():
    system, user = PromptRegistry().render("test_generation", 1, context="CONTEXT")
    assert "pytest" in system
    assert "CONTEXT" in user


def test_unknown_prompt_raises():
    with pytest.raises(KeyError):
        PromptRegistry().render("nope", 1, context="x")


def test_render_load_verdict():
    _, user = PromptRegistry().render(
        "load_verdict", 1, rps=1, p50=2, p90=3, p99=4, error_rate=0.1, baseline="(нет)"
    )
    assert "p99" in user
    assert "4" in user
