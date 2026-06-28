"""
Streamlit チャット UI。

FastAPI の POST /chat（SSE）を httpx-sse で受信して
ストリーミング表示する。

【画面構成】
  - サイドバー : 設定（FastAPI URL / ツール一覧表示）
  - メイン     : チャット履歴 + 入力フォーム
"""

import os

import httpx
import streamlit as st
from httpx_sse import connect_sse

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://fastapi:8000")

# ──────────────────────────────────────────────
# ページ設定
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="MCP Agent Chat",
    page_icon="🤖",
    layout="wide",
)

# ──────────────────────────────────────────────
# セッション状態の初期化
# ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tool_events" not in st.session_state:
    st.session_state.tool_events = []

# ──────────────────────────────────────────────
# サイドバー
# ──────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ 設定")
    st.markdown(f"**FastAPI URL**: `{FASTAPI_URL}`")

    st.divider()

    # 利用可能ツール一覧を取得
    st.subheader("🔧 利用可能ツール")
    if st.button("ツール一覧を更新"):
        try:
            resp = httpx.get(f"{FASTAPI_URL}/tools", timeout=5)
            tools = resp.json().get("tools", [])
            for t in tools:
                st.markdown(f"- **{t['name']}**: {t['description']}")
        except Exception as e:
            st.error(f"取得失敗: {e}")

    st.divider()

    # 履歴クリア
    if st.button("🗑️ 会話をクリア"):
        st.session_state.messages = []
        st.session_state.tool_events = []
        st.rerun()

    st.divider()
    st.caption("LangGraph + FastMCP + Streamlit 学習用サンプル")

# ──────────────────────────────────────────────
# メインエリア
# ──────────────────────────────────────────────
st.title("🤖 MCP Agent Chat")

# 過去メッセージの表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ──────────────────────────────────────────────
# ユーザー入力 & エージェント応答
# ──────────────────────────────────────────────
if prompt := st.chat_input("メッセージを入力してください"):

    # ユーザーメッセージを表示・保存
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # エージェント応答（SSE ストリーミング）
    with st.chat_message("assistant"):
        placeholder = st.empty()
        tool_placeholder = st.empty()
        full_response = ""
        active_tools = []

        try:
            with httpx.Client(timeout=60) as client:
                with connect_sse(
                    client,
                    "POST",
                    f"{FASTAPI_URL}/chat",
                    json={
                        "message": prompt,
                        "history": st.session_state.messages[:-1],
                    },
                ) as event_source:
                    for sse_event in event_source.iter_sse():

                        if sse_event.event == "tool_call":
                            # ツール呼び出し通知
                            tool_name = sse_event.data
                            active_tools.append(tool_name)
                            tool_placeholder.info(
                                f"🔧 ツール実行中: `{', '.join(active_tools)}`"
                            )

                        elif sse_event.event == "done":
                            tool_placeholder.empty()
                            break

                        elif sse_event.data and sse_event.data != "[DONE]":
                            # テキストチャンク
                            full_response += sse_event.data
                            placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

        except Exception as e:
            full_response = f"❌ エラーが発生しました: {e}"
            placeholder.markdown(full_response)

    # アシスタントメッセージを保存
    if full_response:
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )
