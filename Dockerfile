FROM python:3.11-slim

# 基本ツールとChromiumのインストール
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ設定
WORKDIR /app

# 依存関係ファイルのコピー
COPY requirements.txt .

# Pythonライブラリのインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY . .

# ポートの公開
EXPOSE 8501

# 環境変数の設定
ENV CHROMIUM_PATH=/usr/bin/chromium
ENV PORT=8501

# アプリケーションの起動コマンド
CMD streamlit run app.py --server.port $PORT --server.address 0.0.0.0
