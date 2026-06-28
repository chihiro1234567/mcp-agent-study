"""
LangGraph の State 定義。

MessagesState を継承することで
messages フィールドに append reducer が自動で付く。
追加フィールドを増やすときはここに足す。
"""

from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """
    messages : HumanMessage / AIMessage / ToolMessage のリスト
               （MessagesState が add_messages reducer を提供）

    勉強用に追加したいフィールド例:
        tool_calls_count: int = 0   # 何回ツールを呼んだか
        last_tool_used: str = ""    # 最後に使ったツール名
    """
    pass
