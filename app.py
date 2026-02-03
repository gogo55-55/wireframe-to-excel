import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image, ImageDraw, ImageFont
import io
import time
import os
import tempfile

# ==========================================
# 設定・定数
# ==========================================
APP_TITLE = "Wireframe to Excel Specification Generator"
SHEET1_NAME = "原稿入力シート"
SHEET2_NAME = "ワイヤー確認用"

# 日本語フォントパス（環境に合わせて自動検出）
import platform

def get_japanese_font_path():
    """環境に応じた日本語フォントパスを返す"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        # macOSの日本語フォント候補
        mac_fonts = [
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        ]
        for font_path in mac_fonts:
            if os.path.exists(font_path):
                return font_path
    elif system == "Windows":
        # Windowsの日本語フォント候補
        win_fonts = [
            "C:/Windows/Fonts/meiryo.ttc",
            "C:/Windows/Fonts/msgothic.ttc",
            "C:/Windows/Fonts/YuGothM.ttc",
        ]
        for font_path in win_fonts:
            if os.path.exists(font_path):
                return font_path
    else:  # Linux
        linux_fonts = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK.ttc",
            "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
            "/usr/share/fonts/truetype/takao-gothic/TakaoGothic.ttf",
        ]
        for font_path in linux_fonts:
            if os.path.exists(font_path):
                return font_path
    
    return None  # 見つからない場合はNone

FONT_PATH = get_japanese_font_path()

def setup_driver():
    """Headless Chromeの設定"""
    chrome_options = Options()
    chrome_options.add_argument("--headless") # 画面を出さずに実行
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1280,800") # 初期ウィンドウサイズ
    
    # Streamlit Cloud（Linux）の場合はChromiumのパスを指定
    if os.path.exists("/usr/bin/chromium"):
        chrome_options.binary_location = "/usr/bin/chromium"
    elif os.path.exists("/usr/bin/chromium-browser"):
        chrome_options.binary_location = "/usr/bin/chromium-browser"
    
    try:
        # webdriver-managerを使用してChromeDriverを自動管理
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.core.os_manager import ChromeType
        
        # Chromiumを使う場合
        if chrome_options.binary_location:
            service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        else:
            service = Service(ChromeDriverManager().install())
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        # フォールバック: 直接Chromeを使用
        print(f"webdriver-manager failed: {e}, trying direct Chrome")
        driver = webdriver.Chrome(options=chrome_options)
    
    return driver

def get_full_page_screenshot(driver):
    """ページ全体のスクリーンショットを取得"""
    # ページの実際の高さを取得
    total_height = driver.execute_script("return document.body.scrollHeight")
    viewport_width = driver.execute_script("return document.body.scrollWidth")
    
    # ウィンドウサイズをページ全体に合わせる
    driver.set_window_size(max(1280, viewport_width), total_height)
    time.sleep(0.5)  # リサイズ後のレンダリング待ち
    
    # スクリーンショット取得
    return driver.get_screenshot_as_png()

def draw_annotations(screenshot_bytes, elements_data):
    """スクリーンショットに矢印とIDを描画する"""
    image = Image.open(io.BytesIO(screenshot_bytes))
    draw = ImageDraw.Draw(image)
    
    # フォント読み込み（失敗したらデフォルト）
    font = None
    font_small = None
    
    if FONT_PATH and os.path.exists(FONT_PATH):
        try:
            font = ImageFont.truetype(FONT_PATH, 26)
            font_small = ImageFont.truetype(FONT_PATH, 22)  # 右側ラベル用（大きめ）
        except Exception as e:
            print(f"フォント読み込みエラー: {e}")
    
    if font is None:
        # デフォルトフォントを使用（日本語は表示されない可能性あり）
        try:
            font = ImageFont.truetype("Arial", 26)
            font_small = ImageFont.truetype("Arial", 22)
        except:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()

    # 右側の余白を作るためにカンバスを広げる
    margin_right = 400
    new_width = image.width + margin_right
    new_image = Image.new("RGB", (new_width, image.height), "white")
    new_image.paste(image, (0, 0))
    
    draw = ImageDraw.Draw(new_image)
    
    # 要素をY座標順にソート（上から順番に並ぶように）
    sorted_elements = sorted(elements_data, key=lambda x: x['y'])
    
    # 矢印の色リスト（交互に使用して識別しやすく）
    colors = [
        "#E60012",  # 赤
        "#0066CC",  # 青
        "#009944",  # 緑
        "#FF6600",  # オレンジ
        "#9933CC",  # 紫
        "#00A0E9",  # シアン
        "#E4007F",  # マゼンタ
        "#8B4513",  # ブラウン
    ]
    
    # ラベルの重なりを防ぐためのY座標計算
    label_height = 35  # 各ラベルの高さ
    used_positions = []  # 使用済みY位置
    
    def get_non_overlapping_y(target_y):
        """重ならないY座標を取得（要素の高さに近い位置を優先）"""
        candidate_y = max(10, target_y - 12)  # 要素の中心に近い位置から開始
        
        # 既存のラベルと重ならないようにずらす
        max_attempts = 50
        for _ in range(max_attempts):
            is_overlapping = False
            for pos in used_positions:
                if abs(candidate_y - pos) < label_height:
                    is_overlapping = True
                    candidate_y = pos + label_height
                    break
            if not is_overlapping:
                break
        
        used_positions.append(candidate_y)
        return candidate_y
    
    def draw_arrow(draw, start, end, color, width=3):
        """矢印を描画する（終端に三角形）"""
        import math
        
        # 線を描画
        draw.line([start, end], fill=color, width=width)
        
        # 矢印の頭（三角形）を描画
        arrow_size = 12
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        
        # 三角形の3点を計算
        p1 = end
        p2 = (end[0] - arrow_size * math.cos(angle - math.pi/6),
              end[1] - arrow_size * math.sin(angle - math.pi/6))
        p3 = (end[0] - arrow_size * math.cos(angle + math.pi/6),
              end[1] - arrow_size * math.sin(angle + math.pi/6))
        
        draw.polygon([p1, p2, p3], fill=color)
    
    # 丸数字のリスト（スクリーンショット用 - ソート後に順番に割り当て）
    circle_numbers = ['①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩',
                      '⑪','⑫','⑬','⑭','⑮','⑯','⑰','⑱','⑲','⑳',
                      '㉑','㉒','㉓','㉔','㉕','㉖','㉗','㉘','㉙','㉚',
                      '㉛','㉜','㉝','㉞','㉟','㊱','㊲','㊳','㊴','㊵',
                      '㊶','㊷','㊸','㊹','㊺','㊻','㊼','㊽','㊾','㊿']

    # 矢印とIDの描画
    for i, item in enumerate(sorted_elements):
        # 色を順番に使用
        color = colors[i % len(colors)]
        
        # 要素のY座標に近い位置にラベルを配置
        target_y = item['y'] + (item['height'] / 2)
        label_x = image.width + 20
        label_y = get_non_overlapping_y(target_y)
        
        # ソート後の順番で丸数字を表示（①②③...）
        display_id = circle_numbers[i] if i < len(circle_numbers) else f"({i + 1})"
        
        # 1. 右側のIDボックス（丸数字 + ラベル）
        text = f"{display_id}: {item['label'][:12]}" if len(item['label']) > 12 else f"{display_id}: {item['label']}"
        
        # 背景を描画（読みやすくするため）
        try:
            bbox = draw.textbbox((label_x, label_y), text, font=font_small)
            draw.rectangle(bbox, fill="white", outline=color, width=1)
        except:
            pass
        
        draw.text((label_x, label_y), text, fill=color, font=font_small)
        
        # 2. 対象要素への矢印
        # 要素の右端中央
        arrow_target_x = item['x'] + item['width']
        arrow_target_y = item['y'] + (item['height'] / 2)
        
        # 矢印を引く (右のラベルから要素へ)
        start_point = (label_x - 5, label_y + 12)
        end_point = (arrow_target_x + 5, arrow_target_y)
        draw_arrow(draw, start_point, end_point, color, width=3)
        
        # 要素を囲む枠線
        draw.rectangle(
            [(item['x'], item['y']), (item['x'] + item['width'], item['y'] + item['height'])],
            outline=color, width=3
        )

    return new_image

def process_html_to_excel(html_content):
    """HTMLを解析してExcelバイナリを返すメイン処理"""
    
    # 1. 一時ファイルとしてHTMLを保存
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        tmp.write(html_content)
        tmp_path = tmp.name

    driver = setup_driver()
    data_rows = []
    
    try:
        # 2. ブラウザで開く
        driver.get(f"file://{tmp_path}")
        time.sleep(1) # レンダリング待ち

        # 3. 解析と座標取得 (JavaScriptで正確な位置を取得)
        # data-labelを持つ要素を探す
        elements = driver.find_elements("css selector", "[data-label]")
        
        elements_meta = []
        
        # 丸数字のリスト（①〜㊿まで対応）
        circle_numbers = ['①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩',
                          '⑪','⑫','⑬','⑭','⑮','⑯','⑰','⑱','⑲','⑳',
                          '㉑','㉒','㉓','㉔','㉕','㉖','㉗','㉘','㉙','㉚',
                          '㉛','㉜','㉝','㉞','㉟','㊱','㊲','㊳','㊴','㊵',
                          '㊶','㊷','㊸','㊹','㊺','㊻','㊼','㊽','㊾','㊿']
        
        # 除外するキーワード（画像/写真関連 - 全セクション共通）
        exclude_keywords_all = ['写真', '画像', 'フォト', 'photo', 'image', 'img', 'ビジュアル', 'MV', '背景']
        
        # ヒーローセクションのみ除外するキーワード
        exclude_keywords_hero = ['大見出し', 'サブタイトル', 'タイトル', '見出し英語', '見出しEN', '見出し']
        
        item_count = 0  # 有効な要素のカウント
        
        for idx, elem in enumerate(elements):
            # 表示されていない要素（titleなど）は座標取得でエラーになるため除外するかチェック
            if not elem.is_displayed():
                continue

            # data属性から情報取得
            section = elem.get_attribute("data-section") or ""  # セクション名
            label = elem.get_attribute("data-label") or ""  # 要素名
            limit = elem.get_attribute("data-limit") or ""  # 文字数制限
            text = elem.text.strip()
            
            # 写真・画像関連は全セクションで除外
            if any(keyword.lower() in label.lower() for keyword in exclude_keywords_all):
                continue
            
            # ヒーローセクションの見出し関連は除外
            if 'ヒーロー' in section.lower() or 'hero' in section.lower():
                if any(keyword.lower() in label.lower() for keyword in exclude_keywords_hero):
                    continue
            
            # 座標取得
            rect = elem.rect # x, y, width, height
            
            # 一旦座標付きでリストに追加（後でソートしてID割り当て）
            elements_meta.append({
                "section": section,
                "label": label,
                "text": text,
                "limit": limit,
                "x": rect['x'],
                "y": rect['y'],
                "width": rect['width'],
                "height": rect['height']
            })
        
        # Y座標でソート（上から順番に）
        elements_meta.sort(key=lambda x: x['y'])
        
        # ソート後に丸数字を割り当て
        for i, item in enumerate(elements_meta):
            if i < len(circle_numbers):
                row_id = circle_numbers[i]
            else:
                row_id = f"({i + 1})"  # 50以上の場合は(51)形式
            
            # IDを追加
            item['id'] = row_id
            
            # Excelデータに追加
            data_rows.append({
                "ID": row_id,
                "セクション": item['section'],
                "要素": item['label'],
                "ワイヤー記載（参考）": item['text'],
                "クライアント入力": "",
                "文字数目安": item['limit'],
                "現在文字数": ""  # Excel関数で後から設定
            })

        # 4. スクリーンショット撮影（ページ全体）
        png = get_full_page_screenshot(driver)
        
    finally:
        driver.quit()
        os.remove(tmp_path)

    # 5. 画像加工（矢印描画）
    annotated_img = draw_annotations(png, elements_meta)
    
    # 6. Excel生成
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: リスト
        df = pd.DataFrame(data_rows)
        df.to_excel(writer, sheet_name=SHEET1_NAME, index=False)
        
        # Sheet 1の装飾
        worksheet1 = writer.sheets[SHEET1_NAME]
        
        # 列幅設定
        worksheet1.column_dimensions['A'].width = 12  # ID
        worksheet1.column_dimensions['B'].width = 16  # セクション
        worksheet1.column_dimensions['C'].width = 16  # 要素
        worksheet1.column_dimensions['D'].width = 45  # ワイヤー記載（参考）
        worksheet1.column_dimensions['E'].width = 45  # クライアント入力
        worksheet1.column_dimensions['F'].width = 10  # 文字数目安
        worksheet1.column_dimensions['G'].width = 10  # 現在文字数
        
        # スタイル定義
        # ヘッダー行（緑背景、白文字、太字）
        header_fill = PatternFill(start_color='4A7C59', end_color='4A7C59', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF')
        header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        # クライアント入力列（黄色背景）
        input_fill = PatternFill(start_color='FFFDE7', end_color='FFFDE7', fill_type='solid')
        input_alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        
        # 通常セル（折り返しあり）
        normal_alignment = Alignment(vertical='top', wrap_text=True)
        
        # 枠線
        thin_border = Border(
            left=Side(style='thin', color='CCCCCC'),
            right=Side(style='thin', color='CCCCCC'),
            top=Side(style='thin', color='CCCCCC'),
            bottom=Side(style='thin', color='CCCCCC')
        )
        
        # ヘッダー行のスタイル適用
        for cell in worksheet1[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = thin_border
        
        # データ行のスタイル適用
        for row_idx, row in enumerate(worksheet1.iter_rows(min_row=2, max_row=worksheet1.max_row), start=2):
            # 行の高さを設定（テキストが長い場合に対応）
            worksheet1.row_dimensions[row_idx].height = 50
            
            for cell in row:
                cell.alignment = normal_alignment
                cell.border = thin_border
                
                # クライアント入力列（E列）は黄色背景
                if cell.column_letter == 'E':
                    cell.fill = input_fill
                    cell.alignment = input_alignment
                
                # 現在文字数列（G列）にLEN関数を設定
                if cell.column_letter == 'G':
                    cell.value = f'=LEN(E{row_idx})'
                    cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # ヘッダー行の高さ
        worksheet1.row_dimensions[1].height = 30
        
        # 固定（フリーズ）ヘッダー行
        worksheet1.freeze_panes = 'A2'
        
        # Sheet 2: 画像貼り付け
        # ダミーのDataFrameでシート作成
        pd.DataFrame(["以下画像参照"]).to_excel(writer, sheet_name=SHEET2_NAME, index=False, header=False)
        worksheet2 = writer.sheets[SHEET2_NAME]
        
        # 画像をBytesIOに保存してExcelに貼る
        img_byte_arr = io.BytesIO()
        annotated_img.save(img_byte_arr, format='PNG')
        img_to_excel = openpyxl_image(img_byte_arr)
        
        worksheet2.add_image(img_to_excel, 'A1')

    output.seek(0)
    return output

# OpenPyXLのスタイル関連インポート
from openpyxl.drawing.image import Image as openpyxl_image
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

# ==========================================
# UI構築 (Streamlit)
# ==========================================
st.set_page_config(page_title="ワイヤー原稿ツール", layout="wide")

st.title("📑 ワイヤーフレーム原稿依頼書ジェネレーター")
st.markdown("""
HTMLファイルをアップロードすると、以下のファイルを作成します。
1. **原稿入力シート**: クライアント記入用のExcelリスト
2. **確認用シート**: どこに何が入るか、矢印付きのワイヤー画像
""")

uploaded_file = st.file_uploader("HTMLファイルをドラッグ＆ドロップ", type=["html", "htm"])

if uploaded_file is not None:
    st.info("ファイルを解析中... ブラウザレンダリングを実行しています")
    
    try:
        # アップロードされたファイルを読み込む
        html_bytes = uploaded_file.read()
        
        # HTMLファイル名からExcelファイル名を生成
        original_filename = uploaded_file.name  # 例: 会社概要.html
        base_name = original_filename.rsplit('.', 1)[0]  # 拡張子を除去
        excel_filename = f"{base_name}.xlsx"  # 例: 会社概要.xlsx
        
        # 処理実行
        excel_file = process_html_to_excel(html_bytes)
        
        st.success(f"生成完了！ファイル名: **{excel_filename}**")
        
        # ダウンロードボタン
        st.download_button(
            label=f"📥 {excel_filename} をダウンロード",
            data=excel_file,
            file_name=excel_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")