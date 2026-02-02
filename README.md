# 📑 ワイヤーフレーム原稿依頼書ジェネレーター

HTMLワイヤーフレームからExcel原稿入力シートを自動生成するツールです。

## 🚀 機能

- **原稿入力シート**: クライアント記入用のExcelリスト
- **確認用シート**: どこに何が入るか、矢印付きのワイヤー画像

## 📋 使い方

1. HTMLファイルをアップロード
2. 自動で解析・スクリーンショット撮影
3. Excelファイルをダウンロード

## 🔧 ローカルで実行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📁 ファイル構成

```
├── app.py              # メインアプリケーション
├── requirements.txt    # Python依存関係
├── packages.txt        # システム依存関係（Chromium）
└── .streamlit/         # Streamlit設定
    └── config.toml
```

## ⚠️ 注意事項

- HTMLには `data-section` と `data-label` 属性が必要です
- ヒーローセクションは400px以下を推奨

## 📝 AI Studio連携

AI Studioでワイヤーフレームを生成する際は、`AI_STUDIO_SYSTEM_INSTRUCTIONS.md` のルールを使用してください。
