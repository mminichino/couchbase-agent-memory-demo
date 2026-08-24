from __future__ import annotations

import json
import logging
import os
from typing import Any, Callable

import agentc
from agentc_core.activity.models.content import ToolCallContent, ToolResultContent
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field, create_model

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = """
You are a helpful assistant with access to Couchbase Agent Memory, Couchbase data
through an MCP server, and web search.

Answer the user's question clearly and directly.

Tool policy:
- Retrieve flight schedules from the MCP server. Flight records are in the
  `flights` collection in the `travel` bucket and `data` scope.
- Use `web_search` for current, recent, live, or time-sensitive information.
- Use `search_memory` when an answer may depend on a preference, fact, or prior
  conversation that the user previously shared.
- Use `store_memory` for durable preferences, stable traits, and important
  facts that should be available in future sessions.
- Do not store trivial or temporary details as durable facts.
- Completed chat turns are automatically written to the current session by the
  application. Do not call `add_working_memory` yourself.
- Prefer a tool call over guessing when external or stored information is needed.

Response style:
- Answer the user's actual question first.
- Be conversational and natural.
- When the user shares information, acknowledge it without adding unsolicited advice.
- State recalled information naturally rather than describing memory internals.
- Respond to flight availability and schedule requests as a travel assistant.
  Use stored travel preferences in memory if available to personalize the response.
""".strip()

AuditCallback = Callable[[dict[str, Any]], Any]


class _NullSpan:
    def new(self, name: str, **kwargs: Any) -> "_NullSpan":
        return self

    def enter(self) -> "_NullSpan":
        return self

    def exit(self) -> None:
        return None

    def log(self, content: Any) -> None:
        return None


def turn_span_for(catalog: agentc.Catalog | None, session_id: str) -> Any:
    if catalog is None:
        return _NullSpan()
    return catalog.Span(name="chat_turn", session=session_id)


__all__ = [
    "AuditCallback",
    "DEFAULT_SYSTEM_PROMPT",
    "build_catalog",
    "catalog_tool_to_langchain",
    "load_catalog_tools",
    "load_system_prompt",
    "log_tool_call",
    "log_tool_result",
    "turn_span_for",
]


def _schema_type(field_schema: dict[str, Any]) -> Any:
    schema_type = field_schema.get("type", "string")
    if schema_type == "integer":
        return int
    if schema_type == "number":
        return float
    if schema_type == "boolean":
        return bool
    if schema_type == "array":
        return list[Any]
    return str


def _args_model_from_schema(name: str, schema: dict[str, Any]) -> type[BaseModel]:
    properties = schema.get("properties") or {}
    required = set(schema.get("required") or [])
    fields: dict[str, Any] = {}
    for field_name, field_schema in properties.items():
        if not isinstance(field_schema, dict):
            continue
        description = field_schema.get("description", "")
        if field_name in required:
            fields[field_name] = (
                _schema_type(field_schema),
                Field(..., description=description),
            )
        else:
            fields[field_name] = (
                _schema_type(field_schema) | None,
                Field(default=None, description=description),
            )
    if not fields:
        return create_model(f"{name.title()}Args")
    return create_model(f"{name.title()}Args", **fields)


def build_catalog() -> agentc.Catalog | None:
    secrets = {
        "CB_CONN_STRING": os.getenv(
            "CB_CONN_STRING",
            os.getenv("AGENT_CATALOG_CONN_STRING", "couchbase://couchbase-demo"),
        ),
        "CB_USERNAME": os.getenv(
            "CB_USERNAME",
            os.getenv("AGENT_CATALOG_USERNAME", "Administrator"),
        ),
        "CB_PASSWORD": os.getenv(
            "CB_PASSWORD",
            os.getenv("AGENT_CATALOG_PASSWORD", "password"),
        ),
    }
    try:
        return agentc.Catalog(secrets=secrets)
    except ValueError as exc:
        logger.warning("Agent Catalog unavailable: %s", exc)
        return None


def load_system_prompt(catalog: agentc.Catalog | None) -> str:
    if catalog is None:
        return DEFAULT_SYSTEM_PROMPT
    try:
        prompt = catalog.find("prompt", name="travel_assistant_system")
    except Exception as exc:
        logger.warning("Could not load catalog prompt: %s", exc)
        return DEFAULT_SYSTEM_PROMPT

    if prompt is None:
        logger.warning("Catalog prompt travel_assistant_system not found; using default.")
        return DEFAULT_SYSTEM_PROMPT

    content = prompt.content
    if isinstance(content, dict):
        instructions = content.get("agent_instructions")
        if isinstance(instructions, list):
            return "\n".join(str(item) for item in instructions).strip()
        if isinstance(instructions, str):
            return instructions.strip()
        return json.dumps(content, ensure_ascii=False)
    return str(content).strip()


def catalog_tool_to_langchain(tool: agentc.Tool) -> StructuredTool:
    schema = tool.input or {"type": "object", "properties": {}}
    args_schema = _args_model_from_schema(tool.meta.name, schema)

    def _invoke(**kwargs: Any) -> Any:
        return tool.func(**kwargs)

    async def _ainvoke(**kwargs: Any) -> Any:
        return tool.func(**kwargs)

    return StructuredTool.from_function(
        func=_invoke,
        coroutine=_ainvoke,
        name=tool.meta.name,
        description=tool.meta.description,
        args_schema=args_schema,
    )


def load_catalog_tools(catalog: agentc.Catalog | None) -> list[BaseTool]:
    if catalog is None:
        return []
    tools: list[BaseTool] = []
    for tool_name in ("flights_by_route",):
        try:
            tool = catalog.find("tool", name=tool_name)
        except Exception as exc:
            logger.warning("Could not load catalog tool %s: %s", tool_name, exc)
            continue
        if tool is None:
            logger.warning("Catalog tool %s not found.", tool_name)
            continue
        tools.append(catalog_tool_to_langchain(tool))
    return tools


def log_tool_call(
    span: agentc.Span,
    *,
    name: str,
    args: dict[str, Any],
    tool_call_id: str,
) -> None:
    span.log(
        ToolCallContent(
            tool_name=name,
            tool_args=args,
            tool_call_id=tool_call_id,
            status="success",
        )
    )


def log_tool_result(
    span: agentc.Span,
    *,
    name: str,
    result: Any,
    tool_call_id: str,
    status: str,
    duration_ms: float,
) -> None:
    span.log(
        ToolResultContent(
            tool_call_id=tool_call_id,
            tool_result=result,
            status="success" if status == "success" else "error",
        )
    )
