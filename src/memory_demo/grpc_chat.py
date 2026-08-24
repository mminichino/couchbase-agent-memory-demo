from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import sys
from typing import AsyncIterator

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s [%(filename)s:%(lineno)d]",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

import grpc
import grpc.aio
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, message_to_dict

from memory_demo import chat_service_pb2
from memory_demo import chat_service_pb2_grpc
from memory_demo.driver import ChatWithMemory
from memory_demo.mcp_tools import DEFAULT_MCP_SERVER_URL

logger = logging.getLogger()

DEFAULT_PORT = 8088


def _base_message_to_json(msg: BaseMessage) -> str:
    return json.dumps(message_to_dict(msg), ensure_ascii=False)


class ChatGrpcServicer(chat_service_pb2_grpc.ChatServiceServicer):
    def __init__(self, chat_factory) -> None:
        self._chat_factory = chat_factory

    async def ProcessInput(
        self,
        request: chat_service_pb2.ProcessInputRequest, # noqa
        context: grpc.aio.ServicerContext,
    ) -> AsyncIterator[chat_service_pb2.BaseMessageChunk]: # noqa
        audit_queue: asyncio.Queue[dict | None] = asyncio.Queue()

        async def on_audit(event: dict) -> None:
            await audit_queue.put(event)

        chat = self._chat_factory(on_audit=on_audit)
        owns_chat = True

        async def run_chat() -> None:
            try:
                async for msg in chat.process_input_async(
                    request.content,
                    request.session_id,
                    request.user_id,
                ):
                    if not isinstance(msg, BaseMessage):
                        continue
                    await audit_queue.put(
                        {
                            "__message__": chat_service_pb2.BaseMessageChunk(
                                message_json=_base_message_to_json(msg)
                            )
                        }
                    )
            except Exception as e:
                logger.error(f"ProcessInput failed: {e}")
                await audit_queue.put({"__error__": str(e)})
            finally:
                await audit_queue.put(None)
                if owns_chat:
                    await chat.aclose()

        worker = asyncio.create_task(run_chat())

        try:
            while True:
                item = await audit_queue.get()
                if item is None:
                    break
                if "__error__" in item:
                    await context.abort(grpc.StatusCode.INTERNAL, item["__error__"])
                    return
                if "__message__" in item:
                    yield item["__message__"]
                    continue
                yield chat_service_pb2.BaseMessageChunk(
                    audit_json=json.dumps(item, ensure_ascii=False, default=str)
                )
        finally:
            if not worker.done():
                worker.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await worker


class _SharedChatFactory:
    def __init__(self, chat: ChatWithMemory) -> None:
        self._chat = chat

    def __call__(self, on_audit=None) -> ChatWithMemory:
        if on_audit is None:
            return self._chat
        return ChatWithMemory(
            ams_url=self._chat.ams_url,
            mcp_server_url=self._chat.mcp_server_url,
            enable_sync_methods=False,
            smart_model=self._chat.smart_model,
            on_audit=on_audit,
        )


async def serve(port: int, chat: ChatWithMemory | None = None) -> None:
    load_dotenv()
    ams_url = os.getenv("AGENT_MEMORY_SERVER_URL", "http://localhost:8080")
    mcp_server_url = os.getenv("MCP_SERVER_URL", DEFAULT_MCP_SERVER_URL)
    owns_chat = chat is None
    chat = chat or ChatWithMemory(
        ams_url=ams_url,
        mcp_server_url=mcp_server_url,
        enable_sync_methods=False,
    )
    factory = _SharedChatFactory(chat)

    server = grpc.aio.server()
    chat_service_pb2_grpc.add_ChatServiceServicer_to_server(
        ChatGrpcServicer(factory),
        server,
    )
    listen = f"[::]:{port}"
    server.add_insecure_port(listen)
    await server.start()
    logger.info(
        "gRPC ChatService listening on %s "
        "(AGENT_MEMORY_SERVER_URL=%s, MCP_SERVER_URL=%s)",
        listen,
        ams_url,
        mcp_server_url,
    )
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("gRPC ChatService terminated by user")
        await server.stop(0)
    finally:
        if owns_chat:
            await chat.aclose()


def main() -> None:
    p = int(os.getenv("GRPC_PORT", str(DEFAULT_PORT)))
    asyncio.run(serve(p))


if __name__ == "__main__":
    main()
