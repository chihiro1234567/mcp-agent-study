"""
FastAPI エントリポイント
- POST /chat        : メッセージ送信（SSE ストリーミング）
- GET  /health      : ヘルスチェック
- GET  /tools       : 利用可能なMCPツール一覧
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.graph import build_graph
from mcp_client.client import get_tools

app = FastAPI(title="MCP Agent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []   # [{"role": "user"|"assistant", "content": "..."}]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/tools")
async def list_tools():
    """FastMCP サーバーから取得できるツール一覧を返す"""
    tools = await get_tools()
    return {"tools": [{"name": t.name, "description": t.description} for t in tools]}


@app.post("/chat")
async def chat(req: ChatRequest):
    """
    LangGraph Agent を実行し、SSE（text/event-stream）でトークンを逐次返す。
    Streamlit 側は httpx-sse でこのストリームを受信する。
    """
    graph = await build_graph()

    async def event_stream():
        messages = []
        for h in req.history:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": req.message})

        async for chunk in graph.astream(
            {"messages": messages},
            stream_mode="messages",
        ):
            # chunk は (message_chunk, metadata) のタプル
            msg_chunk, _ = chunk
            if hasattr(msg_chunk, "content") and msg_chunk.content:
                content = msg_chunk.content
                if isinstance(content, str) and content:
                    yield f"data: {content}\n\n"
            # ツール呼び出しイベントをクライアントに通知
            if hasattr(msg_chunk, "tool_calls") and msg_chunk.tool_calls:
                for tc in msg_chunk.tool_calls:
                    yield f"event: tool_call\ndata: {tc['name']}\n\n"

        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
