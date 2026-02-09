FROM python:3.11-slim

# 基本ツールとChromium、日本語フォントのインストール
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    chromium \
    chromium-driver \
    fonts-noto-cjk \
    locales \
    && rm -rf /var/lib/apt/lists/*

# 日本語ロケールの設定
RUN localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LC_ALL ja_JP.UTF-8

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
