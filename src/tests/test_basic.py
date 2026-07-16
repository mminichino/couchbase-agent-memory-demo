import os
import uuid

from dotenv import load_dotenv
import pytest
from memory_demo.driver import ChatWithMemory


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="requires Couchbase Agent Memory, OpenAI, and Tavily services",
)
def test_single_chat_message() -> None:
    load_dotenv()
    ams_url = os.getenv("AGENT_MEMORY_SERVER_URL", "http://localhost:8080")
    chat = ChatWithMemory(ams_url=ams_url)

    try:
        messages = list(
            chat.process_input(
                "What is the current weather in San Francisco?",
                str(uuid.uuid4()),
                "pytest",
            )
        )
        assert any(message.type == "ai" for message in messages)
    finally:
        chat.close()
