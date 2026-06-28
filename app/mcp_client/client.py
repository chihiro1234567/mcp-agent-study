"""
MCP Client。

FastMCP サーバー（SSE）に接続し、ツール一覧を LangChain の BaseTool
形式に変換して返す。

langchain-mcp-adapters が提供する MultiServerMCPClient を使うことで
「MCPツール → LangChain BaseTool」への変換を自動化できる。

【接続フロー】
  MultiServerMCPClient
    └─ SSE接続 → FastMCP :8001
         └─ tools/list → FastMCPが返すツール定義
              └─ LangChain BaseTool に変換
"""

import os
from functools import lru_cache

from langchain_mcp_adapters.client import MultiServerMCPClient


def _get_mcp_url() -> str:
    return os.getenv("MCP_SERVER_URL", "http://mcp-server:8001/sse")


async def get_tools():
    """
    FastMCP サーバーからツール一覧を取得して LangChain ツールとして返す。

    MultiServerMCPClient はコンテキストマネージャとして使うのが本来の形だが、
    ここではシンプルに都度接続して取得する（学習用）。
    """
    mcp_url = _get_mcp_url()

    async with MultiServerMCPClient(
        {
            "mcp-server": {
                "url": mcp_url,
                "transport": "sse",
            }
        }
    ) as client:
        tools = client.get_tools()

    return tools
