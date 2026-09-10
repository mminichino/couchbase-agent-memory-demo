import pytest

from memory_demo.llm_config import (
    ANTHROPIC_OPENAI_BASE_URL,
    DEFAULT_CLAUDE_MODEL,
    DEFAULT_OPENAI_MODEL,
    resolve_llm_config,
)


def test_resolve_openai_when_openai_key_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")
    monkeypatch.setenv("AGENTMEMORY_LLM_API_KEY", "sk-ant-ignored")
    monkeypatch.delenv("AGENTMEMORY_LLM_MODEL", raising=False)
    monkeypatch.delenv("AGENTMEMORY_LLM_URL", raising=False)
    config = resolve_llm_config()
    assert config.provider == "openai"
    assert config.model == DEFAULT_OPENAI_MODEL
    assert config.api_key == "sk-openai-test"
    assert config.base_url is None


def test_resolve_anthropic_via_llm_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("AGENTMEMORY_LLM_API_KEY", "sk-ant-test")
    monkeypatch.delenv("AGENTMEMORY_LLM_MODEL", raising=False)
    monkeypatch.delenv("AGENTMEMORY_LLM_URL", raising=False)
    config = resolve_llm_config()
    assert config.provider == "anthropic"
    assert config.model == DEFAULT_CLAUDE_MODEL
    assert config.api_key == "sk-ant-test"
    assert config.base_url == ANTHROPIC_OPENAI_BASE_URL


def test_resolve_model_and_url_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("AGENTMEMORY_LLM_API_KEY", "sk-ant-test")
    monkeypatch.setenv("AGENTMEMORY_LLM_MODEL", "claude-opus-5")
    monkeypatch.setenv("AGENTMEMORY_LLM_URL", "https://example.com/v1/")
    config = resolve_llm_config()
    assert config.provider == "anthropic"
    assert config.model == "claude-opus-5"
    assert config.base_url == "https://example.com/v1/"


def test_resolve_requires_a_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AGENTMEMORY_LLM_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY|AGENTMEMORY_LLM_API_KEY"):
        resolve_llm_config()
