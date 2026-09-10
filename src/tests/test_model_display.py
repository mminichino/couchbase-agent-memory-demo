import pytest

from memory_demo.model_display import get_model_display_info


def test_openai_display(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
    monkeypatch.delenv("AGENTMEMORY_LLM_API_KEY", raising=False)
    monkeypatch.delenv("AGENTMEMORY_LLM_MODEL", raising=False)
    monkeypatch.delenv("AGENTMEMORY_LLM_URL", raising=False)
    monkeypatch.delenv("AGENTMEMORY_EMBEDDING_URL", raising=False)
    monkeypatch.delenv("AGENTMEMORY_EMBEDDING_MODEL", raising=False)
    info = get_model_display_info()
    assert info.llm_provider == "OpenAI"
    assert info.llm_model == "gpt-5.4"
    assert info.embedding_model == "text-embedding-3-small"
    assert info.embedding_provider == "OpenAI"


def test_claude_capella_embedding_display(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("AGENTMEMORY_LLM_API_KEY", "sk-ant")
    monkeypatch.setenv("AGENTMEMORY_LLM_MODEL", "claude-sonnet-5")
    monkeypatch.setenv("AGENTMEMORY_LLM_URL", "https://api.anthropic.com/v1/")
    monkeypatch.setenv(
        "AGENTMEMORY_EMBEDDING_URL",
        "https://xbxg79oc1emidd.ai.cloud.couchbase.com",
    )
    monkeypatch.setenv(
        "AGENTMEMORY_EMBEDDING_MODEL",
        "nvidia/llama-3.2-nv-embedqa-1b-v2",
    )
    info = get_model_display_info()
    assert info.llm_provider == "Anthropic"
    assert info.llm_model == "claude-sonnet-5"
    assert info.embedding_model == "nvidia/llama-3.2-nv-embedqa-1b-v2"
    assert info.embedding_provider == "Capella"


def test_custom_embedding_display(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
    monkeypatch.setenv("AGENTMEMORY_EMBEDDING_URL", "https://other.example.com/v1")
    monkeypatch.setenv("AGENTMEMORY_EMBEDDING_MODEL", "custom-embed")
    info = get_model_display_info()
    assert info.embedding_provider == "Custom"
    assert info.embedding_model == "custom-embed"
