"""Resolve chat LLM settings for OpenAI or Claude (Anthropic).

Selection uses Agent Memory env vars (no custom AMS entrypoint):

- If ``OPENAI_API_KEY`` is set, use OpenAI (``gpt-5.4`` by default).
- Else if ``AGENTMEMORY_LLM_API_KEY`` is set, treat that key as Anthropic/Claude
  (``claude-sonnet-5`` via ``AGENTMEMORY_LLM_URL``, defaulting to
  ``https://api.anthropic.com/v1/``).

Optional overrides: ``AGENTMEMORY_LLM_MODEL``, ``AGENTMEMORY_LLM_URL``.
Embeddings for Agent Memory are configured separately via
``AGENTMEMORY_EMBEDDING_*`` / ``OPENAI_API_KEY``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from langchain_openai import ChatOpenAI

DEFAULT_OPENAI_MODEL = "gpt-5.4"
DEFAULT_CLAUDE_MODEL = "claude-sonnet-5"
ANTHROPIC_OPENAI_BASE_URL = "https://api.anthropic.com/v1/"

Provider = Literal["anthropic", "openai"]


@dataclass(frozen=True)
class LLMConfig:
    provider: Provider
    model: str
    api_key: str
    base_url: str | None

    def build_chat_model(self) -> ChatOpenAI:
        kwargs: dict = {
            "model": self.model,
            "api_key": self.api_key,
        }
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return ChatOpenAI(**kwargs)


def resolve_llm_config() -> LLMConfig:
    """Prefer OpenAI when ``OPENAI_API_KEY`` is set; else Claude via AMS LLM key."""
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    llm_api_key = (os.getenv("AGENTMEMORY_LLM_API_KEY") or "").strip()
    model_override = (os.getenv("AGENTMEMORY_LLM_MODEL") or "").strip() or None
    url_override = (os.getenv("AGENTMEMORY_LLM_URL") or "").strip() or None

    if openai_key:
        return LLMConfig(
            provider="openai",
            model=model_override or DEFAULT_OPENAI_MODEL,
            api_key=openai_key,
            base_url=url_override,
        )

    if llm_api_key:
        return LLMConfig(
            provider="anthropic",
            model=model_override or DEFAULT_CLAUDE_MODEL,
            api_key=llm_api_key,
            base_url=url_override or ANTHROPIC_OPENAI_BASE_URL,
        )

    raise ValueError(
        "Set OPENAI_API_KEY (OpenAI) or AGENTMEMORY_LLM_API_KEY (Claude) for the chat LLM."
    )


def build_chat_model(config: LLMConfig | None = None) -> ChatOpenAI:
    return (config or resolve_llm_config()).build_chat_model()
