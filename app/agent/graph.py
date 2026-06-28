"""
LangGraph StateGraph の組み立て。

【グラフ構造】
  START
    │
    ▼
  llm_node   ◀──────────────┐
    │                        │
    ├─(tool_calls あり)──▶ tool_node
    │                        │
    └─(tool_calls なし)──▶ END

【学習ポイント】
- add_node()  : ノードを登録
- add_edge()  : 固定エッジ（常にこちらへ）
- add_conditional_edges() : 条件付きエッジ（関数の戻り値で分岐）
- compile()   : グラフを実行可能オブジェクトに変換
"""

import os

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from agent.nodes import make_llm_node, make_tool_node, should_continue
from agent.state import AgentState
from mcp_client.client import get_tools


def _build_llm():
    """環境変数でOllama/OpenRouterを切り替える"""
    provider = os.getenv("LLM_PROVIDER", "ollama")

    if provider == "openrouter":
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-haiku"),
            temperature=0,
            streaming=True,
        )
    else:
        # デフォルト: Ollama（ローカル）
        return ChatOllama(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434"),
            model=os.getenv("OLLAMA_MODEL", "gemma4:26b"),
            temperature=0,
        )


async def build_graph():
    """
    MCP ツールを取得し、LangGraph を組み立てて返す。
    リクエストごとに呼ばれるが、ツール取得はキャッシュ可（今回はシンプルに毎回取得）。
    """
    # 1. MCP Server からツール一覧を取得
    tools = await get_tools()

    # 2. LLM にツールをバインド
    llm = _build_llm()
    llm_with_tools = llm.bind_tools(tools)

    # 3. グラフ定義
    graph_builder = StateGraph(AgentState)

    # ノード登録
    graph_builder.add_node("llm", make_llm_node(llm_with_tools))
    graph_builder.add_node("tools", make_tool_node(tools))

    # エッジ登録
    graph_builder.add_edge(START, "llm")

    graph_builder.add_conditional_edges(
        "llm",
        should_continue,
        {
            "tools": "tools",   # ツール呼び出しあり → tool_node へ
            "end": END,         # 回答完了 → 終了
        },
    )

    graph_builder.add_edge("tools", "llm")  # ツール実行後は必ず llm へ戻る

    # 4. コンパイル
    return graph_builder.compile()
