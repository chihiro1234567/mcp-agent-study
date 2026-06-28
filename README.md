# MCP Agent Study

LangGraph + FastMCP + Streamlit の勉強用サンプルプロジェクト。

## 構成

```
Streamlit :8501
    ↕ HTTP (SSE)
FastAPI :8000  ← LangGraph Agent + MCP Client
    ↕ LLM呼び出し (ChatOllama / ChatOpenAI)
Ollama :11434 (ホスト) / OpenRouter (外部API)
    ↕ SSE (HTTP)
FastMCP :8001  ← ツール実装
    ↕ ファイル/SQLite アクセス
./data/        ← volume mount
```

## クイックスタート

### 1. 環境ファイルを作成

```bash
cp .env.example .env
# .env を編集して LLM プロバイダーを設定
```

### 2. Ollama を使う場合（ローカルLLM）

```bash
# ホスト側で Ollama を起動してモデルをダウンロード
ollama pull gemma4:26b
```

ollamaが起動しているか確認

```bash
systemctl status ollama

● ollama.service - Ollama Service
     Loaded: loaded (/etc/systemd/system/ollama.service; enabled; preset: enabled)
     Active: active (running) since Sun 2026-06-28 14:01:13 JST; 4h 8min ago
   Main PID: 1677 (ollama)
      Tasks: 20 (limit: 57506)
```


### 3. OpenRouter を使う場合（クラウドLLM）

`.env` を編集：
```
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxx
```

### 4. 起動

```bash
docker compose up --build
```

### 5. ブラウザでアクセス

- **チャット UI** : http://localhost:8501
- **FastAPI docs**: http://localhost:8000/docs
- **FastMCP SSE** : http://localhost:8001/sse

## 試してみるプロンプト例

| 操作 | プロンプト |
|------|-----------|
| ファイル読み | `hello.txt の内容を読んで` |
| ファイル書き | `memo.txt に買い物リストを書いて` |
| DB 作成 | `notes テーブルを作成して` |
| DB 書き込み | `"LangGraph の勉強中" という内容を notes に保存して` |
| DB 参照 | `notes テーブルの内容を見せて` |
| 検索（stub）| `MCP とは何か調べて` |

## ファイル構成

```
mcp-agent-study/
├── docker-compose.yml
├── .env.example
├── data/
│   └── files/          # FastMCP がアクセスするファイル置き場
│       └── hello.txt
├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py             # FastAPI エントリポイント
│   ├── agent/
│   │   ├── state.py        # AgentState（MessagesState を継承）
│   │   ├── nodes.py        # llm_node / tool_node / should_continue
│   │   └── graph.py        # StateGraph の組み立て
│   ├── mcp_client/
│   │   └── client.py       # MultiServerMCPClient で SSE 接続
│   └── ui/
│       └── streamlit_app.py
└── mcp_server/
    ├── Dockerfile
    ├── requirements.txt
    └── server.py           # @mcp.tool() でツールを定義
```

## 学習ポイント

### LangGraph
- `StateGraph` にノードとエッジを登録してグラフを定義する
- `should_continue` でツール呼び出しの有無を判断して分岐
- `add_conditional_edges` で動的ルーティング
- `astream(stream_mode="messages")` でトークンをリアルタイム取得

### MCP
- `MultiServerMCPClient` で SSE 接続 → `get_tools()` で LangChain ツールに変換
- FastMCP の `@mcp.tool()` は型アノテーション + docstring がスキーマになる

### 拡張アイデア
- `AgentState` にフィールドを追加してツール呼び出し回数を記録する
- `web_search` を Tavily/SerpAPI の実装に差し替える
- `langchain-mcp-adapters` を `stdio` モードに切り替えて挙動を比較する
- LangGraph の `MemorySaver` でセッションをまたいだ会話履歴を保持する
