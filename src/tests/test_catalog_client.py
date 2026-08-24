from __future__ import annotations

from memory_demo.catalog_client import (
    DEFAULT_SYSTEM_PROMPT,
    build_catalog,
    load_system_prompt,
    turn_span_for,
)


def test_load_system_prompt_without_catalog() -> None:
    assert load_system_prompt(None) == DEFAULT_SYSTEM_PROMPT


def test_turn_span_without_catalog() -> None:
    span = turn_span_for(None, "session-1")
    child = span.new(name="child")
    child.enter()
    child.log("ignored")
    child.exit()


def test_build_catalog_without_local_index(monkeypatch) -> None:
    monkeypatch.delenv("AGENT_CATALOG_CONN_STRING", raising=False)
    monkeypatch.delenv("AGENT_CATALOG_BUCKET", raising=False)
    assert build_catalog() is None
