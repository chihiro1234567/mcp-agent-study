"""
FastMCP Server。

@mcp.tool() デコレータで関数を MCP ツールとして公開する。
型アノテーションと docstring が自動でツール定義（スキーマ）になる。

【起動方法】
  python server.py
  → SSE エンドポイント: http://0.0.0.0:8001/sse

【実装ツール】
  1. list_files  : ディレクトリ内のファイル一覧
  2. read_file   : ファイルの内容を読む
  3. write_file  : ファイルに内容を書く
  4. query_db    : SQLite に SELECT/INSERT/CREATE などを実行
  5. web_search  : Web検索（スタブ。実APIに切り替え可能）
"""

import json
import os
import sqlite3
from pathlib import Path

from fastmcp import FastMCP

# FastMCP インスタンス生成
mcp = FastMCP(name="study-mcp-server")

# リソースのベースパス（docker-compose で /data をマウント）
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
FILES_DIR = DATA_DIR / "files"
DB_PATH = DATA_DIR / "study.db"

# ディレクトリがなければ作成
FILES_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════
# ツール 1: ファイル一覧
# ══════════════════════════════════════════════
@mcp.tool()
def list_files(directory: str = "") -> str:
    """
    指定ディレクトリのファイル一覧を返す。
    directory を省略すると /data/files/ 直下を対象にする。

    Args:
        directory: 一覧を取得するサブディレクトリ名（省略可）

    Returns:
        ファイル名のリスト（JSON文字列）
    """
    target = FILES_DIR / directory if directory else FILES_DIR
    if not target.exists():
        return json.dumps({"error": f"ディレクトリが存在しません: {directory}"})

    entries = []
    for p in sorted(target.iterdir()):
        entries.append({
            "name": p.name,
            "type": "dir" if p.is_dir() else "file",
            "size": p.stat().st_size if p.is_file() else None,
        })
    return json.dumps(entries, ensure_ascii=False)


# ══════════════════════════════════════════════
# ツール 2: ファイル読み取り
# ══════════════════════════════════════════════
@mcp.tool()
def read_file(filename: str) -> str:
    """
    指定したファイルの内容を文字列で返す。

    Args:
        filename: 読み取るファイル名（例: "memo.txt"）

    Returns:
        ファイルの内容（テキスト）
    """
    path = FILES_DIR / filename
    if not path.exists():
        return f"エラー: ファイルが見つかりません: {filename}"
    if not path.is_file():
        return f"エラー: {filename} はファイルではありません"

    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"エラー: ファイル読み取り失敗: {e}"


# ══════════════════════════════════════════════
# ツール 3: ファイル書き込み
# ══════════════════════════════════════════════
@mcp.tool()
def write_file(filename: str, content: str) -> str:
    """
    指定したファイルに内容を書き込む（上書き）。

    Args:
        filename: 書き込むファイル名（例: "memo.txt"）
        content : 書き込む内容

    Returns:
        成功/失敗メッセージ
    """
    path = FILES_DIR / filename
    # サブディレクトリがあれば作成
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        path.write_text(content, encoding="utf-8")
        return f"書き込み完了: {filename} ({len(content)} 文字)"
    except Exception as e:
        return f"エラー: 書き込み失敗: {e}"


# ══════════════════════════════════════════════
# ツール 4: SQLite クエリ実行
# ══════════════════════════════════════════════
@mcp.tool()
def query_db(sql: str) -> str:
    """
    SQLite データベースに SQL を実行して結果を返す。
    SELECT / INSERT / CREATE TABLE / UPDATE / DELETE が使える。

    Args:
        sql: 実行する SQL 文

    Returns:
        SELECT の場合は結果行のJSON。それ以外は影響行数。

    Example:
        CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, text TEXT)
        INSERT INTO notes (text) VALUES ('Hello MCP')
        SELECT * FROM notes
    """
    try:
        con = sqlite3.connect(str(DB_PATH))
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute(sql)

        sql_upper = sql.strip().upper()
        if sql_upper.startswith("SELECT") or sql_upper.startswith("PRAGMA"):
            rows = [dict(row) for row in cur.fetchall()]
            con.close()
            return json.dumps(rows, ensure_ascii=False, default=str)
        else:
            con.commit()
            affected = cur.rowcount
            con.close()
            return f"実行完了: {affected} 行が影響を受けました"

    except Exception as e:
        return f"SQLエラー: {e}"


# ══════════════════════════════════════════════
# ツール 5: Web 検索（スタブ）
# ══════════════════════════════════════════════
@mcp.tool()
def web_search(query: str, max_results: int = 3) -> str:
    """
    Web 検索を行い結果を返す。
    ※ 現在はスタブ実装。実際の検索APIに差し替え可能。

    差し替え候補:
      - Tavily API  : pip install tavily-python
      - SerpAPI     : pip install google-search-results
      - DuckDuckGo  : pip install duckduckgo-search

    Args:
        query      : 検索クエリ
        max_results: 返す件数（デフォルト3）

    Returns:
        検索結果のJSON（title, url, snippet）
    """
    # --- スタブ: ダミーデータを返す ---
    stub_results = [
        {
            "title": f"[スタブ] {query} に関する記事 {i+1}",
            "url": f"https://example.com/search?q={query}&page={i+1}",
            "snippet": f"これは '{query}' に関するダミー検索結果です。"
                       f"実際の検索APIに差し替えることで本物の結果が得られます。",
        }
        for i in range(max_results)
    ]
    return json.dumps(stub_results, ensure_ascii=False)


# ══════════════════════════════════════════════
# エントリポイント
# ══════════════════════════════════════════════
if __name__ == "__main__":
    print(f"FastMCP Server 起動中... DATA_DIR={DATA_DIR}")
    print(f"  FILES_DIR : {FILES_DIR}")
    print(f"  DB_PATH   : {DB_PATH}")
    print("  SSE endpoint: http://0.0.0.0:8001/sse")

    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=8001,
    )
