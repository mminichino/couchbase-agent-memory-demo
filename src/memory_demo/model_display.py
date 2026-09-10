"""Resolve LLM/embedding display labels for the Session details pane."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from memory_demo.llm_config import (
    ANTHROPIC_OPENAI_BASE_URL,
    DEFAULT_CLAUDE_MODEL,
    DEFAULT_OPENAI_MODEL,
)

DEFAULT_OPENAI_EMBEDDING = "text-embedding-3-small"
ANTHROPIC_HOST = "api.anthropic.com"


@dataclass(frozen=True)
class ModelDisplayInfo:
    llm_provider: str
    llm_model: str
    embedding_model: str
    embedding_provider: str


def _non_empty(value: str | None) -> str | None:
    trimmed = (value or "").strip()
    return trimmed or None


def _hostname(url: str) -> str:
    try:
        return urlparse(url).hostname or url
    except Exception:
        return url.removeprefix("https://").removeprefix("http://").split("/")[0] or url


def _label_for_embedding_url(url: str) -> str:
    host = _hostname(url)
    return "Capella" if host.endswith("ai.cloud.couchbase.com") else "Custom"


def _llm_provider_label(base_url: str | None) -> str:
    if not base_url:
        return "OpenAI"
    host = _hostname(base_url)
    if host == ANTHROPIC_HOST or host.endswith(".anthropic.com"):
        return "Anthropic"
    if host.endswith("ai.cloud.couchbase.com"):
        return "Capella"
    return "Custom"


def get_model_display_info() -> ModelDisplayInfo:
    openai_key = _non_empty(os.getenv("OPENAI_API_KEY"))
    llm_api_key = _non_empty(os.getenv("AGENTMEMORY_LLM_API_KEY"))
    llm_model = _non_empty(os.getenv("AGENTMEMORY_LLM_MODEL"))
    llm_url = _non_empty(os.getenv("AGENTMEMORY_LLM_URL"))
    embedding_model = _non_empty(os.getenv("AGENTMEMORY_EMBEDDING_MODEL"))
    embedding_url = _non_empty(os.getenv("AGENTMEMORY_EMBEDDING_URL"))

    if openai_key:
        return ModelDisplayInfo(
            llm_provider=_llm_provider_label(llm_url),
            llm_model=llm_model or DEFAULT_OPENAI_MODEL,
            embedding_model=embedding_model or DEFAULT_OPENAI_EMBEDDING,
            embedding_provider=(
                _label_for_embedding_url(embedding_url) if embedding_url else "OpenAI"
            ),
        )

    if llm_api_key:
        return ModelDisplayInfo(
            llm_provider=_llm_provider_label(llm_url or ANTHROPIC_OPENAI_BASE_URL),
            llm_model=llm_model or DEFAULT_CLAUDE_MODEL,
            embedding_model=embedding_model or "—",
            embedding_provider=(
                _label_for_embedding_url(embedding_url) if embedding_url else "—"
            ),
        )

    return ModelDisplayInfo(
        llm_provider="—",
        llm_model="—",
        embedding_model=embedding_model or "—",
        embedding_provider=(
            _label_for_embedding_url(embedding_url) if embedding_url else "—"
        ),
    )
