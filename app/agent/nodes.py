"""
LangGraph のノード定義。

ノード = グラフ上の「処理の単位」。
State を受け取り、更新された State の差分を返す関数。

【ReAct ループの構造】
  llm_node  ──(ツール呼び出しあり)──▶ tool_node ──▶ llm_node ...
            ──(ツール呼び出しなし)──▶ END
"""

from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode

from agent.state import AgentState

SYSTEM_PROMPT = """あなたは親切なAIアシスタントです。
ユーザーの質問に答えるために、必要に応じて以下のツールを使ってください。

利用可能なツール:
- read_file   : ファイルの内容を読み取る
- write_file  : ファイルに内容を書き込む
- list_files  : ディレクトリのファイル一覧を取得する
- query_db    : SQLite データベースにSQLクエリを実行する
- web_search  : Web検索を行う（スタブ実装）

ツールが不要な質問にはそのまま回答してください。
回答は日本語で行ってください。"""


def make_llm_node(llm_with_tools):
    """
    LLM ノードを生成するファクトリ関数。
    llm_with_tools = llm.bind_tools(tools) で作ったオブジェクトを受け取る。
    """
    async def llm_node(state: AgentState) -> dict:
        """
        State の messages を LLM に渡して AIMessage を返す。
        ツール呼び出しが必要な場合は tool_calls が含まれる。
        """
        messages = state["messages"]

        # システムプロンプトを先頭に付与（まだない場合）
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    return llm_node


def make_tool_node(tools):
    """
    ToolNode を生成するファクトリ関数。
    LangGraph の prebuilt ToolNode は tool_calls を自動で実行し
    ToolMessage をリストで返す。
    """
    return ToolNode(tools)


def should_continue(state: AgentState) -> str:
    """
    条件付きエッジ関数。
    最後のメッセージに tool_calls があれば "tools" へ、
    なければ "end" へルーティングする。
    """
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"
