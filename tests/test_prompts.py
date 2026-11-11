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
