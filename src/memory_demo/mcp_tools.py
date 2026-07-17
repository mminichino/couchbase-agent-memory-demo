from __future__ import annotations

import os

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

DEFAULT_MCP_SERVER_URL = "http://127.0.0.1:9001/mcp"

__all__ = ["DEFAULT_MCP_SERVER_URL", "get_mcp_server_url", "get_mcp_tools"]


def get_mcp_server_url(server_url: str | None = None) -> str:
    return server_url or os.getenv("MCP_SERVER_URL", DEFAULT_MCP_SERVER_URL)


async def get_mcp_tools(server_url: str | None = None) -> list[BaseTool]:
    client = MultiServerMCPClient(
        {
            "couchbase": {
                "transport": "streamable_http",
                "url": get_mcp_server_url(server_url),
            }
        }
    )
    return await client.get_tools(server_name="couchbase")
