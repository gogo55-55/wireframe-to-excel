# 🛠️ セットアップガイド

ワイヤーフレーム原稿依頼書ジェネレーターのインストール手順です。

---

## 📋 必要なもの

1. **Python 3.11** （3.12以上は非推奨）
2. **Google Chrome** ブラウザ

---

## 🚀 インストール手順

### Step 1: フォルダを解凍
ダウンロードしたZIPファイルを解凍してください。

### Step 2: ターミナルを開く
- **Mac**: Spotlight（⌘+スペース）で「ターミナル」と入力して開く
- **Windows**: スタートメニューで「コマンドプロンプト」または「PowerShell」を開く

### Step 3: フォルダに移動
```bash
cd /解凍したフォルダのパス
```
（例: `cd ~/Downloads/wireframe-to-excel`）

### Step 4: 必要なライブラリをインストール
```bash
pip install -r requirements.txt
```

### Step 5: アプリを起動
```bash
streamlit run app.py
```

### Step 6: ブラウザで開く
自動でブラウザが開きます。開かない場合は以下のURLにアクセス：
```
http://localhost:8501
```

---

## 🔧 トラブルシューティング

### 「pip が見つかりません」エラー
```bash
python -m pip install -r requirements.txt
```

### 「streamlit が見つかりません」エラー
```bash
python -m streamlit run app.py
```

### Chrome関連のエラー
Google Chromeがインストールされているか確認してください。

---

## 📝 使い方

1. HTMLファイルをドラッグ&ドロップ
2. 自動で解析・スクリーンショット撮影
3. Excelファイルをダウンロード

---

## ❓ お問い合わせ

不明点があれば担当者までご連絡ください。
