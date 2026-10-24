"""LLM adapters. AnthropicLLM calls the real API; StubLLM is for tests (no network)."""
import os
from dataclasses import dataclass


@dataclass
class LLMResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""


class AnthropicLLM:
    def __init__(self, model: str | None = None, max_tokens: int = 1200):
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover
            raise SystemExit("pip install anthropic") from e
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise SystemExit("Set ANTHROPIC_API_KEY (see .env.example)")
        self.client = anthropic.Anthropic()
        self.model = model or os.environ.get("PE_QA_MODEL", "claude-sonnet-5-5")
        self.max_tokens = max_tokens

    def complete(self, system: str, user: str) -> LLMResult:
        r = self.client.messages.create(
            model=self.model, max_tokens=self.max_tokens,
            system=system, messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        return LLMResult(text, r.usage.input_tokens, r.usage.output_tokens, r.model)


class StubLLM:
    """Returns a fixed string (or the result of a callable) so pipeline logic can be tested offline."""
    def __init__(self, response):
        self.response = response

    def complete(self, system: str, user: str) -> LLMResult:
        text = self.response(system, user) if callable(self.response) else self.response
        return LLMResult(text, 0, 0)
