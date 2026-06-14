"""LLM client abstraction with an offline mock.

The orchestrator only needs ``LLM.complete(prompt) -> str``. ``MockLLM`` makes the
whole demo runnable with no API key (deterministic, for tests + a quick look);
swap in ``AnthropicLLM`` for the real thing.
"""
from __future__ import annotations

import os
import re
from typing import Protocol


class LLM(Protocol):
    def complete(self, prompt: str) -> str: ...


class MockLLM:
    """Offline stand-in. Emits a plausible pytest skeleton by reading the function
    names out of the prompt — enough to demo the agent graph without a key."""

    def complete(self, prompt: str) -> str:
        funcs = re.findall(r"def\s+([a-zA-Z_]\w*)\s*\(", prompt)
        funcs = [f for f in funcs if not f.startswith("test_")]
        if not funcs:
            return "def test_placeholder():\n    assert True\n"
        lines = []
        for fn in dict.fromkeys(funcs):  # dedupe, keep order
            lines += [
                f"def test_{fn}_runs():",
                f"    # TODO: real assertion for {fn}()",
                f"    assert callable({fn})",
                "",
            ]
        return "\n".join(lines)


class AnthropicLLM:
    """Real client. Requires ``pip install anthropic`` and ``ANTHROPIC_API_KEY``."""

    def __init__(self, model: str = "claude-sonnet-4-6"):
        import anthropic  # lazy import so the mock path needs no dependency

        self._client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self._model = model

    def complete(self, prompt: str) -> str:
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text


def default_llm() -> LLM:
    """``AnthropicLLM`` when a key is present, else the offline ``MockLLM``."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return AnthropicLLM()
        except Exception:
            pass
    return MockLLM()
