from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import traceback
from asyncio import AbstractEventLoop
from typing import Any, AsyncGenerator, Generator, Sequence

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolCall,
    ToolMessage,
)
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_fixed

from memory_demo.memory_tools import MemoryToolProvider
from memory_demo.web_search_tools import web_search_function

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

load_dotenv()

SYSTEM_PROMPT = """
You are a helpful assistant with access to Couchbase Agent Memory and web search.

Answer the user's question clearly and directly.

Tool policy:
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
"""

MAX_TOOL_ITERATIONS = 10


class ChatWithMemory:
    def __init__(
        self,
        smart_model: str = "gpt-5.4",
        ams_url: str = "http://localhost:8080",
        enable_sync_methods: bool = True,
        smart_chat_model: BaseChatModel | None = None,
    ) -> None:
        self.error_count = 0
        self.smart_model = smart_model
        self.ams_url = ams_url
        self._base_smart_llm = smart_chat_model or ChatOpenAI(model=smart_model)
        self.memory_client = MemoryToolProvider(
            base_url=ams_url,
            timeout=30.0,
            verify=False,
        )

        self.loop: AbstractEventLoop | None = None
        if enable_sync_methods:
            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)

    def event_loop(self) -> AbstractEventLoop:
        if self.loop is None:
            raise ValueError("Synchronous methods are disabled for this client.")
        if self.loop.is_running():
            raise RuntimeError(
                "process_input() cannot run on an active event loop; "
                "use process_input_async() instead."
            )
        return self.loop

    def increment_error_count(self) -> None:
        self.error_count += 1
        logger.error(traceback.format_exc())

    def _available_functions(
        self,
        user_id: str,
        session_id: str,
    ) -> list[StructuredTool]:
        available_functions: list[StructuredTool] = self.memory_client.get_tools(
            user_id,
            session_id,
        )
        if os.getenv("TAVILY_API_KEY"):
            available_functions.append(web_search_function)
            logger.info("Tavily key present. Web search enabled.")
        else:
            logger.info("Tavily key not present. Web search disabled.")
        return available_functions

    @staticmethod
    def _assistant_content_str(message: Any) -> str:
        content = getattr(message, "content", message)
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and "text" in block:
                    parts.append(str(block["text"]))
                else:
                    parts.append(str(block))
            return "".join(parts).strip()
        return str(content).strip() if content is not None else ""

    @staticmethod
    def normalize_messages(
        messages: Sequence[dict[str, Any] | BaseMessage],
    ) -> list[BaseMessage]:
        normalized: list[BaseMessage] = []
        for message in messages:
            if not isinstance(message, dict):
                normalized.append(message)
                continue

            role = message.get("role")
            content = message.get("content", "")
            if role == "system":
                normalized.append(SystemMessage(content=content))
            elif role == "user":
                normalized.append(HumanMessage(content=content))
            elif role == "assistant":
                tool_calls = message.get("tool_calls")
                normalized.append(
                    AIMessage(
                        content=content or "",
                        tool_calls=(
                            ChatWithMemory._openai_tool_blocks_to_lc(tool_calls)
                            if tool_calls
                            else []
                        ),
                    )
                )
            elif role == "tool":
                normalized.append(
                    ToolMessage(
                        content=content if isinstance(content, str) else str(content),
                        tool_call_id=message.get("tool_call_id", ""),
                        name=message.get("name") or "",
                    )
                )
        return normalized

    @staticmethod
    def _openai_tool_blocks_to_lc(
        blocks: Sequence[Any],
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for index, block in enumerate(blocks):
            if not isinstance(block, dict):
                continue
            if block.get("name") and "args" in block:
                normalized.append(
                    {
                        "name": block["name"],
                        "args": ChatWithMemory._tool_call_args_as_dict(block["args"]),
                        "id": block.get("id", f"tool_call_{index}"),
                        "type": "tool_call",
                    }
                )
                continue
            function = block.get("function")
            if block.get("type") == "function" and isinstance(function, dict):
                normalized.append(
                    {
                        "name": function.get("name", ""),
                        "args": ChatWithMemory._tool_call_args_as_dict(
                            function.get("arguments", {})
                        ),
                        "id": block.get("id", f"tool_call_{index}"),
                        "type": "tool_call",
                    }
                )
        return normalized

    @staticmethod
    def _tool_calls_from_ai_message(
        message: AIMessage,
    ) -> list[ToolCall] | list[dict[str, Any]]:
        if message.tool_calls:
            return list(message.tool_calls)
        raw = (message.additional_kwargs or {}).get("tool_calls") or []
        return ChatWithMemory._openai_tool_blocks_to_lc(raw)

    @staticmethod
    def _tool_call_args_as_dict(args: Any) -> dict[str, Any]:
        if isinstance(args, dict):
            return args
        if isinstance(args, str):
            try:
                parsed = json.loads(args) if args.strip() else {}
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}

    @staticmethod
    def _tool_result_content(result: Any) -> str:
        if isinstance(result, str):
            return result
        if hasattr(result, "model_dump"):
            result = result.model_dump()
        try:
            return json.dumps(result, ensure_ascii=False, default=str)
        except TypeError:
            return str(result)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def query_smart_llm(
        self,
        messages: list[BaseMessage],
        available_functions: list[StructuredTool],
    ) -> AIMessage:
        llm = self._base_smart_llm.bind_tools(available_functions)
        response = await llm.ainvoke([SystemMessage(content=SYSTEM_PROMPT), *messages])
        if not isinstance(response, AIMessage):
            return AIMessage(content=getattr(response, "content", str(response)))
        return response

    async def _generate_response(
        self,
        session_id: str,
        user_id: str,
        context_messages: Sequence[dict[str, Any] | BaseMessage],
        message: str,
    ) -> AsyncGenerator[BaseMessage]:
        conversation = self.normalize_messages(context_messages)
        conversation.append(HumanMessage(content=message))

        available_functions = self._available_functions(user_id, session_id)
        tools_by_name = {tool.name: tool for tool in available_functions}

        for iteration in range(1, MAX_TOOL_ITERATIONS + 1):
            logger.info(
                "Generate: %s (%s), tool iteration %d",
                user_id,
                session_id,
                iteration,
            )
            response = await self.query_smart_llm(
                conversation,
                available_functions,
            )
            tool_calls = self._tool_calls_from_ai_message(response)
            if not tool_calls:
                text = self._assistant_content_str(response)
                if text:
                    working_memory_tool = tools_by_name["add_working_memory"]
                    await working_memory_tool.ainvoke(
                        {
                            "messages": [
                                {
                                    "user_content": message,
                                    "assistant_content": text,
                                }
                            ]
                        }
                    )
                yield AIMessage(content=text)
                return

            conversation.append(response)
            for tool_call in tool_calls:
                name = tool_call.get("name") or ""
                args = self._tool_call_args_as_dict(tool_call.get("args"))
                tool_call_id = tool_call.get("id") or f"tool_call_{iteration}"
                tool = tools_by_name.get(name)
                started_at = time.monotonic()
                status = "success"

                if tool is None:
                    status = "error"
                    content = f"Unknown tool: {name}"
                else:
                    try:
                        logger.info("Calling tool: %s", name)
                        result = await tool.ainvoke(args)
                        content = self._tool_result_content(result)
                    except Exception as exc:
                        self.increment_error_count()
                        logger.exception("Tool '%s' failed", name)
                        status = "error"
                        content = f"Error calling tool '{name}': {exc}"

                tool_message = ToolMessage(
                    content=content,
                    tool_call_id=tool_call_id,
                    name=name,
                    status=status,
                    response_metadata={
                        "execution_time_seconds": time.monotonic() - started_at
                    },
                )
                conversation.append(tool_message)
                yield tool_message

        raise RuntimeError(
            f"Model exceeded the maximum of {MAX_TOOL_ITERATIONS} tool iterations."
        )

    async def process_input_async(
        self,
        content: str,
        session_id: str,
        user_id: str,
    ) -> AsyncGenerator[BaseMessage]:
        logger.info(
            "Process user input: user %s: session %s: message %s",
            user_id,
            session_id,
            content,
        )
        try:
            context_messages = await self.memory_client.get_chat_history(
                user_id,
                session_id,
            )
            async for response in self._generate_response(
                session_id,
                user_id,
                context_messages,
                content,
            ):
                yield response
        except Exception as exc:
            self.increment_error_count()
            logger.exception("Error processing user input: %s", exc)
            yield AIMessage(
                content="I'm sorry, I encountered an error processing your request."
            )

    def process_input(
        self,
        user_input: str,
        session_id: str,
        user_id: str,
    ) -> Generator[BaseMessage, None, None]:
        loop = self.event_loop()
        generator = self.process_input_async(
            user_input,
            session_id,
            user_id,
        )
        try:
            while True:
                try:
                    yield loop.run_until_complete(generator.__anext__())
                except StopAsyncIteration:
                    break
        finally:
            loop.run_until_complete(generator.aclose())

    def close(self) -> None:
        self.memory_client.close()
        self.event_loop().run_until_complete(self.memory_client.aclose())

    async def aclose(self) -> None:
        self.memory_client.close()
        await self.memory_client.aclose()
