"""
Thin OpenAI LLM factory with caching and rate limiting.

This module defines the OpenAIClient class, which is responsible for
instantiating and caching ChatOpenAI instances based on provided settings. It also
applies request-level rate limiting to manage API usage effectively.
"""

from __future__ import annotations
from typing import Optional, Union, Mapping

from langchain_openai import ChatOpenAI
from langchain_core.rate_limiters import InMemoryRateLimiter

from ai.llm.settings import LLMSettings


class OpenAIClient:
    """
    Thin OpenAI LLM factory.

    Responsibilities:
    - Instantiate ChatOpenAI
    - Cache by settings
    - Apply request-level rate limiting

    Does NOT:
    - create agents
    - manage prompts
    - know about tools
    - handle memory
    """

    def __init__(
        self,
        default_settings: Optional[LLMSettings] = None,
        rate_limiter: Optional[InMemoryRateLimiter] = None,
    ):
        self._defaults = default_settings or LLMSettings()
        self._rate_limiter = rate_limiter
        self._cache: dict[tuple, ChatOpenAI] = {}

    def _resolve_settings(
        self,
        settings: Union[LLMSettings, Mapping, str, None],
    ) -> LLMSettings:
        """
        Normalize input into a validated LLMSettings instance.

        Accepted inputs:
        - None              → defaults
        - str               → model override
        - dict / Mapping    → partial overrides
        - LLMSettings       → used as-is
        """
        if settings is None:
            resolved = self._defaults

        elif isinstance(settings, str):
            resolved = self._defaults.copy(update={"model": settings})

        elif isinstance(settings, LLMSettings):
            resolved = settings

        elif isinstance(settings, Mapping):
            resolved = self._defaults.copy(update=dict(settings))

        else:
            raise TypeError(f"Unsupported LLM settings type: {type(settings)}")

        return resolved

    def get_llm(
        self,
        settings: Union[LLMSettings, Mapping, str, None] = None,
    ) -> ChatOpenAI:
        """
        Return a cached ChatOpenAI instance for the given settings.

        Settings may be:
        - None            → defaults
        - str             → model override
        - dict / Mapping  → partial overrides
        - LLMSettings     → full config
        """

        resolved = self._resolve_settings(settings)

        cache_key = (
            resolved.model,
            resolved.temperature,
            resolved.top_p,
            resolved.max_tokens,
            resolved.timeout,
        )

        if cache_key not in self._cache:
            self._cache[cache_key] = ChatOpenAI(
                **resolved.as_kwargs(),
                rate_limiter=self._rate_limiter,
            )

        return self._cache[cache_key]
