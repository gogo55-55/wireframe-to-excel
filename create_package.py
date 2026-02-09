import os
import shutil
from pathlib import Path

def create_distribution_package():
    # 作成するフォルダ名
    dist_dir_name = "配布用_ワイヤー原稿ツール"
    current_dir = Path.cwd()
    dist_dir = current_dir / dist_dir_name

    # コピーするファイルとフォルダのリスト
    files_to_copy = [
        "app.py",
        "requirements.txt",
        "SETUP_GUIDE.md",
        "AI_STUDIO_SYSTEM_INSTRUCTIONS.md"
    ]
    
    dirs_to_copy = [
        ".streamlit"
    ]

    print(f"📦 パッケージ作成を開始します: {dist_dir_name}")

    # フォルダがあれば削除して作り直す
    if dist_dir.exists():
        print(f"   既存のフォルダを削除中... {dist_dir_name}")
        shutil.rmtree(dist_dir)
    
    os.makedirs(dist_dir)
    print(f"✅ フォルダを作成しました")

    # ファイルのコピー
    for filename in files_to_copy:
        src = current_dir / filename
        dst = dist_dir / filename
        if src.exists():
            shutil.copy2(src, dst)
            print(f"   Copy: {filename}")
        else:
            print(f"⚠️ Warning: {filename} が見つかりません")

    # フォルダのコピー
    for dirname in dirs_to_copy:
        src = current_dir / dirname
        dst = dist_dir / dirname
        if src.exists():
            shutil.copytree(src, dst)
            print(f"   Copy dir: {dirname}")
        else:
            print(f"⚠️ Warning: {dirname} が見つかりません")

    print("\n🎉 完了しました！")
    print(f"以下のフォルダをZIP圧縮して共有してください:")
    print(f"📂 {dist_dir}")

if __name__ == "__main__":
    create_distribution_package()
