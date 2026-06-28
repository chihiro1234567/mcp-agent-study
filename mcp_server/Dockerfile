FROM python:3.12-slim

WORKDIR /app

# curlのインストール（root権限が必要なため上部に配置）
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
    
# 非rootユーザーで動かす（セキュリティ向上）
RUN adduser --disabled-password --gecos "" mcpuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# dataディレクトリの所有権を移譲
RUN mkdir -p /data/files && chown -R mcpuser:mcpuser /data

USER mcpuser

ENV PYTHONPATH=/app

CMD ["python", "server.py"]