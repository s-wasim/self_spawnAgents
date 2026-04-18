"""Fake LLM provider for unit tests."""
from __future__ import annotations

from dataclasses import dataclass, field

from aae.schemas.common import ModelID


@dataclass
class FakeLLMProvider:
    """Deterministic LLM. Returns (content, tokens_in, tokens_out)."""

    response_by_model: dict[ModelID, str] = field(default_factory=dict)
    default_content: str = '{"decision": "approve", "rationale": "Deterministic fixture OK. Nothing in payload hits a reject rule and no ambiguity present."}'
    tokens_in: int = 500
    tokens_out: int = 200

    async def call(
        self, *, model: ModelID, system: str, user: str, max_tokens: int
    ) -> tuple[str, int, int]:
        content = self.response_by_model.get(model, self.default_content)
        return content, self.tokens_in, self.tokens_out

    async def complete(self, *, model: ModelID, system: str, user: str) -> str:
        content = self.response_by_model.get(model, self.default_content)
        return content
