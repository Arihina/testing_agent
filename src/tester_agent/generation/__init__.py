"""Generation: LLM-слой — Gateway, Prompt Registry, Synthesizer'ы (§3.2)."""

from .gateway import LLMError, LLMGateway
from .prompts import PromptRegistry
from .repair import RepairSynthesizer
from .synthesizer import TestSynthesizer

__all__ = ["LLMError", "LLMGateway", "PromptRegistry", "RepairSynthesizer", "TestSynthesizer"]
