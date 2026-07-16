from __future__ import annotations

import logging

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from typing import Any, Optional, Union

from agentmemory import (
    AgentMemoryClient,
    AsyncAgentMemoryClient,
    NotFoundError,
    ConflictError,
)
from agentmemory.models import MemoryBlock

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

__all__ = [
    "MemoryToolProvider",
    "build_memory_tools",
    "SearchMemoryArgs",
    "StoreMemoryArgs",
    "AddWorkingMemoryArgs",
    "ListMemoriesArgs",
]


class SearchMemoryArgs(BaseModel):
    query: str = Field(
        ...,
        description="Natural-language description of what to recall from memory, "
        "e.g. 'the user's favorite programming language' or 'past travel plans'.",
    )
    all_sessions: bool = Field(
        False,
        description="Search across all of the user's sessions when true; "
        "otherwise only the current session is searched.",
    )


class StoreMemoryArgs(BaseModel):
    facts: list[str] = Field(
        ...,
        min_length=1,
        description="One or more standalone facts about the user worth remembering "
        "for future conversations (durable preferences, stable traits, important "
        "episodic facts). Each fact should be self-contained.",
    )


class WorkingMemoryMessage(BaseModel):
    user_content: str = Field(..., min_length=1)
    assistant_content: str = Field(..., min_length=1)


class AddWorkingMemoryArgs(BaseModel):
    messages: list[WorkingMemoryMessage] = Field(
        ...,
        min_length=1,
        description="Completed user/assistant chat turns to add to this session's history.",
    )


class ListMemoriesArgs(BaseModel):
    limit: int = Field(
        10,
        ge=1,
        le=200,
        description="Maximum number of recent memories to return.",
    )
    all_sessions: bool = Field(
        False,
        description="List memories from all of the user's sessions when true; "
        "otherwise only the current session.",
    )


class MemoryToolProvider:

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        *,
        token: Union[str, None] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        verify: Union[bool, str] = True,
        sync_client: Optional[AgentMemoryClient] = None,
        async_client: Optional[AsyncAgentMemoryClient] = None,
    ) -> None:
        self._sync_client = sync_client or AgentMemoryClient(
            base_url=base_url,
            token=token,
            timeout=timeout,
            max_retries=max_retries,
            verify=verify,
        )
        self._async_client = async_client or AsyncAgentMemoryClient(
            base_url=base_url,
            token=token,
            timeout=timeout,
            max_retries=max_retries,
            verify=verify,
        )

    def _ensure_session_sync(self, user_id: str, session_id: str):
        client = self._sync_client
        try:
            user = client.get_user(user_id)
        except NotFoundError:
            try:
                user = client.create_user(user_id, name=user_id)
            except ConflictError:
                user = client.get_user(user_id)
        try:
            return user.get_session(session_id)
        except NotFoundError:
            try:
                return user.create_session(session_id)
            except ConflictError:
                return user.get_session(session_id)

    async def _ensure_session_async(self, user_id: str, session_id: str):
        client = self._async_client
        try:
            user = await client.get_user(user_id)
        except NotFoundError:
            try:
                user = await client.create_user(user_id, name=user_id)
            except ConflictError:
                user = await client.get_user(user_id)
        try:
            return await user.get_session(session_id)
        except NotFoundError:
            try:
                return await user.create_session(session_id)
            except ConflictError:
                return await user.get_session(session_id)

    @staticmethod
    def _format_block(block: MemoryBlock) -> str:
        if block.fact:
            text = block.fact
        elif block.message is not None:
            msg = block.message
            text = f"User: {msg.user_content} | Assistant: {msg.assistant_content}"
        elif block.summary:
            text = block.summary
        else:
            text = "(empty memory block)"
        if block.rel_score is not None:
            return f"- {text} (relevance: {block.rel_score:.3f})"
        return f"- {text}"

    @classmethod
    def _format_blocks(cls, blocks: list[MemoryBlock]) -> str:
        if not blocks:
            return "No relevant memories found."
        return "\n".join(cls._format_block(b) for b in blocks)

    async def get_chat_history(
        self,
        user_id: str,
        session_id: str,
        *,
        limit: int = 200,
    ) -> list[dict[str, str]]:
        session = await self._ensure_session_async(user_id, session_id)
        result = await session.list_memories(limit=limit, order_by="ingested_at")
        blocks = sorted(result.memory_blocks, key=lambda block: block.ingested_at)
        history: list[dict[str, str]] = []
        for block in blocks:
            if block.message is None:
                continue
            history.extend(
                [
                    {"role": "user", "content": block.message.user_content},
                    {"role": "assistant", "content": block.message.assistant_content},
                ]
            )
        return history

    def get_tools(self, user_id: str, session_id: str) -> list[StructuredTool]:

        def _search(query: str, all_sessions: bool = False) -> str:
            filters: Optional[dict[str, Any]] = (
                {"session_ids": "all"} if all_sessions else None
            )
            session = self._ensure_session_sync(user_id, session_id)
            result = session.search_memory(query=query, filters=filters)
            return self._format_blocks(result.memory_blocks)

        async def _asearch(query: str, all_sessions: bool = False) -> str:
            filters: Optional[dict[str, Any]] = (
                {"session_ids": "all"} if all_sessions else None
            )
            session = await self._ensure_session_async(user_id, session_id)
            result = await session.search_memory(query=query, filters=filters)
            return self._format_blocks(result.memory_blocks)

        search_tool = StructuredTool.from_function(
            func=_search,
            coroutine=_asearch,
            name="search_memory",
            description=(
                "Semantically search the user's stored memories for relevant "
                "facts, preferences, or prior conversation context. Use this "
                "whenever the answer may depend on something the user told you "
                "earlier rather than asking them to repeat themselves."
            ),
            args_schema=SearchMemoryArgs,
        )

        def _store(facts: list[str]) -> str:
            session = self._ensure_session_sync(user_id, session_id)
            resp = session.add_memory(facts=facts)
            return f"Stored {resp.accepted_count} memory item(s)."

        async def _astore(facts: list[str]) -> str:
            session = await self._ensure_session_async(user_id, session_id)
            resp = await session.add_memory(facts=facts)
            return f"Stored {resp.accepted_count} memory item(s)."

        store_tool = StructuredTool.from_function(
            func=_store,
            coroutine=_astore,
            name="store_memory",
            description=(
                "Persist one or more durable facts about the user to long-term "
                "memory so they can be recalled in future conversations. Store "
                "preferences, stable traits, and important episodic facts; do "
                "not store trivial or temporary details."
            ),
            args_schema=StoreMemoryArgs,
        )

        def _add_working_memory(
            messages: list[WorkingMemoryMessage],
        ) -> str:
            session = self._ensure_session_sync(user_id, session_id)
            payload = [
                message.model_dump() if isinstance(message, WorkingMemoryMessage) else message
                for message in messages
            ]
            resp = session.add_memory(messages=payload)
            return f"Added {resp.accepted_count} chat turn(s) to session memory."

        async def _aadd_working_memory(
            messages: list[WorkingMemoryMessage],
        ) -> str:
            session = await self._ensure_session_async(user_id, session_id)
            payload = [
                message.model_dump() if isinstance(message, WorkingMemoryMessage) else message
                for message in messages
            ]
            resp = await session.add_memory(messages=payload)
            return f"Added {resp.accepted_count} chat turn(s) to session memory."

        add_working_memory_tool = StructuredTool.from_function(
            func=_add_working_memory,
            coroutine=_aadd_working_memory,
            name="add_working_memory",
            description=(
                "Add completed user/assistant chat turns to the current Couchbase "
                "Agent Memory session. The application normally calls this "
                "automatically after producing a response."
            ),
            args_schema=AddWorkingMemoryArgs,
        )

        def _list(limit: int = 10, all_sessions: bool = False) -> str:
            session = self._ensure_session_sync(user_id, session_id)
            session_ids = "all" if all_sessions else None
            result = session.list_memories(limit=limit, session_ids=session_ids)
            return self._format_blocks(result.memory_blocks)

        async def _alist(limit: int = 10, all_sessions: bool = False) -> str:
            session = await self._ensure_session_async(user_id, session_id)
            session_ids = "all" if all_sessions else None
            result = await session.list_memories(limit=limit, session_ids=session_ids)
            return self._format_blocks(result.memory_blocks)

        list_tool = StructuredTool.from_function(
            func=_list,
            coroutine=_alist,
            name="list_memories",
            description=(
                "List the user's most recent stored memories. Use this to review "
                "what is already remembered when a semantic search query is not "
                "specific enough."
            ),
            args_schema=ListMemoriesArgs,
        )

        return [search_tool, store_tool, add_working_memory_tool, list_tool]

    def close(self) -> None:
        self._sync_client.close()

    async def aclose(self) -> None:
        await self._async_client.close()


def build_memory_tools(
    user_id: str,
    session_id: str,
    *,
    base_url: str = "http://localhost:8080",
    sync_client: Optional[AgentMemoryClient] = None,
    async_client: Optional[AsyncAgentMemoryClient] = None,
    **client_kwargs: Any,
) -> list[StructuredTool]:
    provider = MemoryToolProvider(
        base_url=base_url,
        sync_client=sync_client,
        async_client=async_client,
        **client_kwargs,
    )
    return provider.get_tools(user_id, session_id)
