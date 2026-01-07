"""
LLM settings model.

This module defines the LLMSettings class, which encapsulates configuration
parameters for language model instances used in the application.
"""

from pydantic import BaseModel, field_validator


class LLMSettings(BaseModel):
    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    top_p: float = 1.0
    max_tokens: int = 1024
    timeout: int = 30

    @field_validator("temperature", "top_p")
    @classmethod
    def _clamp_01(cls, v: float) -> float:
        if v is None:
            return 0.0
        return max(0.0, min(1.0, float(v)))

    @field_validator("max_tokens")
    @classmethod
    def _cap_max_tokens(cls, v: int) -> int:
        v = int(v)
        return min(v, 2048)

    def as_kwargs(self) -> dict:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
        }
