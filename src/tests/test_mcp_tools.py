from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from memory_demo import mcp_tools


def test_get_mcp_server_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MCP_SERVER_URL", raising=False)
    assert mcp_tools.get_mcp_server_url() == mcp_tools.DEFAULT_MCP_SERVER_URL

    monkeypatch.setenv("MCP_SERVER_URL", "http://mcp.example/mcp")
    assert mcp_tools.get_mcp_server_url() == "http://mcp.example/mcp"
    assert mcp_tools.get_mcp_server_url("http://explicit/mcp") == "http://explicit/mcp"


@pytest.mark.asyncio
async def test_get_mcp_tools_uses_streamable_http(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_tools = AsyncMock(return_value=[])
    client = SimpleNamespace(get_tools=get_tools)

    def make_client(connections: dict[str, object]) -> object:
        assert connections == {
            "couchbase": {
                "transport": "streamable_http",
                "url": "http://mcp.example/mcp",
            }
        }
        return client

    monkeypatch.setattr(mcp_tools, "MultiServerMCPClient", make_client)

    assert await mcp_tools.get_mcp_tools("http://mcp.example/mcp") == []
    get_tools.assert_awaited_once_with(server_name="couchbase")
