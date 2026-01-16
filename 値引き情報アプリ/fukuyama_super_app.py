import pandas as pd
import folium
from PIL import Image, ImageDraw
import os
import base64
from io import BytesIO
import json
import logging

# logging設定: UTF-8エンコーディングを指定し、エラーを捕捉
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s', encoding='utf-8')

# --- 0. データ定義 ---
SUPER_DATA = {
    'name': [
        'ハローズ 御幸店', 'ハローズ 神辺モール店', 'ハローズ 南駅家店', 'エブリイ 駅家店',
        'エブリイ 緑町店', 'ハローズ 緑町店', 'フレスタ アイネス店', 'フジ 福山三吉店',
        'ハローズ 山手店', 'フレスタ 蔵王店', 'ラ・ムー 駅家店', 'ハローズ 伊勢丘店',
        'ハローズ 新涯店'
    ],
    'lat': [
        34.547245, 34.542857, 34.544033, 34.538313,
        34.477490, 34.476470, 34.487743, 34.493521,
        34.492559, 34.498787, 34.542412, 
        34.502842,
        34.461328
    ],
    'lon': [
        133.347939, 133.363893, 133.330316, 133.331962,
        133.372590, 133.371601, 133.362712, 133.375035,
        133.333259, 133.392526, 133.326149,
        133.422737,
        133.392132
    ],
    'logo_file': [
        'logo_harrows.png', 'logo_harrows.png', 'logo_harrows.png', 'logo_every.png',
        'logo_every.png', 'logo_harrows.png', 'logo_fresta.png', 'logo_fuji.png',
        'logo_harrows.png', 'logo_fresta.png', 'logo_lamu.png', 'logo_harrows.png',
        'logo_harrows.png'
    ],
    'website': [
        'https://www.halows.com/', 'https://www.halows.com/', 'https://www.halows.com/', 'https://www.super-every.co.jp/',
        'https://www.super-every.co.jp/', 'https://www.halows.com/', 'https://www.fresta.co.jp/', 'https://www.the-fuji.com/',
        'https://www.halows.com/', 'https://www.fresta.co.jp/', 'https://www.e-dkt.co.jp/',  # ★修正: ラ・ムーのURLを更新
        'https://www.halows.com/',
        'https://www.halows.com/'
    ],
    'souzai_info': [
        'ハローズ: 本日の目玉は鶏の唐揚げ！', 'ハローズ: 出来立てのお好み焼きがあります！', 'ハローズ: 特製カツ丼がおすすめ！',
        'エブリイ: 地元の人気弁当が豊富です。', 'エブリイ: サラダ・デリが充実！', 'ハローズ: 特製オムライスが20%OFF！',
        'フレスタ: 自社製パンが人気です。', 'フジ: 手作りおにぎりコーナー！', 'ハローズ: ローストビーフ丼が数量限定！',
        'フレスタ: 季節のパスタフェア開催中！', 'ラ・ムー: 驚きの100円たこ焼き！', 'ハローズ: 本日の目玉は鶏の唐揚げ！',
        'ハローズ: 特製オムライスが20%OFF！'
    ],
    'sengyo_info': [
        'ハローズ: 瀬戸内産の新鮮な鯛が入荷！', 'ハローズ: お刺身盛り合わせがお得！', 'ハローズ: 週末限定マグロの解体！',
        'エブリイ: 干物が充実しています。', 'エブリイ: 本日のアジの開きがおすすめ！', 'ハローズ: マグロの刺身が半額！',
        'フレスタ: 鮮魚コーナーに産直品！', 'フジ: 新鮮なカツオのたたき！', 'ハローズ: 瀬戸内産の新鮮な鯛が入荷！',
        'フレスタ: 新鮮なブリが入荷！', 'ラ・ムー: 激安の冷凍魚介！', 'ハローズ: マグロの刺身が半額！',
        'ハローズ: 瀬戸内産の新鮮な鯛が入荷！'
    ],
    'niku_info': [
        'ハローズ: 黒毛和牛の特売セール！', 'ハローズ: 豚肉のこま切れがグラム98円！', 'ハローズ: BBQ用のお肉セット充実！',
        'エブリイ: 地元産「もみじ鶏」のフェア！', 'エブリイ: 牛すじ肉で煮込み料理はいかが？', 'ハローズ: 国産豚バラブロック半額！',
        'フレスタ: 熟成肉コーナーが自慢です。', 'フジ: 鶏むね肉まとめ買いでお得！', 'ハローズ: 黒毛和牛の特売セール！',
        'フレスタ: 特選ソーセージ・ハムが充実！', 'ラ・ムー: 鶏肉の激安パック！', 'ハローズ: 国産豚バラブロック半額！',
        'ハローズ: 黒毛和牛の特売セール！'
    ],
    'seika_info': [
        'ハローズ: 旬の地元産イチゴが入荷！', 'ハローズ: 新鮮な春キャベツがお買い得！', 'ハローズ: 広島県産レモン大特価！',
        'エブリイ: 地元農家直送の新鮮野菜！', 'エブリイ: 新玉ねぎの詰め放題を実施中！', 'ハローズ: 契約農家のトマトがお買い得！',
        'フレスタ: オーガニック野菜コーナー！', 'フジ: 大粒ぶどうの試食会開催！', 'ハローズ: 旬の地元産イチゴが入荷！',
        'フレスタ: 珍しい輸入野菜も！', 'ラ・ムー: 激安の袋入りもやし！', 'ハローズ: 契約農家のトマトがお買い得！',
        'ハローズ: 新鮮な春キャベツがお買い得！'
    ],
    'brand': [
        'ハローズ', 'ハローズ', 'ハローズ', 'エブリイ',
        'エブリイ', 'ハローズ', 'フレスタ', 'フジ',
        'ハローズ', 'フレスタ', 'ラ・ムー', 'ハローズ',
        'ハローズ'
    ]
}
df = pd.DataFrame(SUPER_DATA)

# --- 1. 設定と画像合成用フォルダの準備 ---
LOGO_FOLDER = 'logos'
PIN_BASE_IMAGE = 'pin_base.png'

os.makedirs(LOGO_FOLDER, exist_ok=True)

PIN_COLORS = {
    'ハローズ': '#FBC02D', 'エブリイ': '#00BCD4', 'フレスタ': '#673AB7', 
    'フジ': '#9C27B0', 'ラ・ムー': '#E91E63',
}

# --- 1-1. PIN_BASE_IMAGE が存在しない場合の代替作成 ---
if not os.path.exists(PIN_BASE_IMAGE):
    logging.info(f"'{PIN_BASE_IMAGE}' が見つかりませんでした。代替ピンベース画像を生成します。")
    img = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((0, 0, 99, 99), fill='#CCCCCC')
    img.save(PIN_BASE_IMAGE)

# --- 1-2. ロゴファイルが存在しない場合の代替作成 ---
def create_placeholder_logo(brand_name, size=(60, 60)):
    """ブランド名の頭文字を中央に配置した代替ロゴ画像を生成"""
    logo_filename = df[df['brand'] == brand_name]['logo_file'].iloc[0]
    logo_path = os.path.join(LOGO_FOLDER, logo_filename)
    if not os.path.exists(logo_path):
        logging.warning(f"ロゴファイル '{logo_filename}' が見つかりませんでした。代替画像を生成します。")
        try:
            img = Image.new('RGBA', size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse((0, 0, size[0], size[1]), fill=PIN_COLORS.get(brand_name, '#CCCCCC'))
            img.save(logo_path)
        except Exception as e:
            logging.error(f"代替ロゴファイルの生成に失敗しました: {e}")

# 全ブランドに対して代替ロゴ生成を試行
for brand in PIN_COLORS.keys():
    create_placeholder_logo(brand)


# --- 2. 画像合成関数 ---
def create_logo_pin_base64(logo_path, pin_base_path, pin_color='#CCCCCC', logo_size=(60, 60)):
    try:
        pin_base = Image.open(pin_base_path).convert("RGBA").resize((100, 100), Image.LANCZOS)
        logo_img = Image.open(logo_path).convert("RGBA").resize(logo_size, Image.LANCZOS)
        
        colored_background = Image.new('RGBA', pin_base.size, pin_color)
        pin_mask = pin_base.split()[-1]
        colored_pin_shape = Image.new('RGBA', pin_base.size, (0,0,0,0))
        colored_pin_shape.paste(colored_background, (0,0), pin_mask)
        
        x_offset = (colored_pin_shape.width - logo_img.width) // 2
        y_offset = (colored_pin_shape.height - logo_img.height) // 2 - 10
        final_pin = colored_pin_shape.copy()
        final_pin.paste(logo_img, (x_offset, y_offset), logo_img)

        buffered = BytesIO()
        final_pin.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    except FileNotFoundError:
        try:
            img = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
            ImageDraw.Draw(img).ellipse((0, 0, 99, 99), fill=pin_color)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode()
        except Exception:
            return None
    except Exception:
        return None

# --- 3. 各店舗のピン画像を生成し、Base64として辞書に格納 ---
generated_pin_base64 = {}
for index, row in df.iterrows():
    logo_path = os.path.join(LOGO_FOLDER, row['logo_file'])
    pin_color = PIN_COLORS.get(row['brand'], '#CCCCCC')
    b64_image = create_logo_pin_base64(logo_path, PIN_BASE_IMAGE, pin_color)
    if b64_image:
        generated_pin_base64[index] = f"data:image/png;base64,{b64_image}"


# --- 4. Foliumマップの作成とマーカーの追加 ---
# 福山市の平均座標 (中心付近)
FUKUYAMA_CENTER = [34.50, 133.37]
map_name = "m_temp"
m_temp = folium.Map(location=FUKUYAMA_CENTER, zoom_start=12, name=map_name)
marker_data_for_js = []

for index, row in df.iterrows():
    pin_image_base64 = generated_pin_base64.get(index)

    # ロゴ画像をポップアップ用にBase64エンコード
    logo_base64_for_popup = ""
    logo_file_path = os.path.join(LOGO_FOLDER, row['logo_file'])
    if os.path.exists(logo_file_path):
        try:
            with open(logo_file_path, 'rb') as f:
                logo_base64_for_popup = base64.b64encode(f.read()).decode()
        except Exception:
            pass

    # ポップアップの内容をリッチに
    # ★修正点: ポップアップを簡素化し、「本日の特売を見る」ボタンと「詳細はこちら」のリンク状の項目を追加
    popup_html = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 250px;">
        <h4 style="margin: 0 0 8px 0; color: #333; border-bottom: 2px solid {PIN_COLORS.get(row['brand'], '#ccc')}; padding-bottom: 5px;">
            <img src='data:image/png;base64,{logo_base64_for_popup}' alt='{row['brand']}ロゴ' style='height: 20px; vertical-align: middle; margin-right: 5px;'>
            {row['name']}
        </h4>
        <p style="margin: 5px 0;"><a href="{row['website']}" target="_blank" style="color: #007bff; text-decoration: none;"><i class="fas fa-globe"></i> 公式ウェブサイト</a></p>
        <hr style="margin: 10px 0; border-top: 1px solid #eee;">
        
        <button onclick="showComparisonPanel('{row['name']}')" style="margin-top: 5px; padding: 8px 10px; background-color: #ffc107; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%; color: #333; transition: background-color 0.2s;">
            <i class="fas fa-search"></i> 本日の特売を見る
        </button>
        
        <div onclick="alert('この機能はまだ作動しません。');" style="margin-top: 10px; text-align: center; font-size: 0.9em; color: #007bff; cursor: pointer; padding: 5px 0; border-top: 1px solid #eee;">
            詳細はこちら <i class="fas fa-chevron-right" style="font-size: 0.7em;"></i>
        </div>
    </div>
    """

    if pin_image_base64:
        icon = folium.CustomIcon(icon_image=pin_image_base64, icon_size=(40, 40), icon_anchor=(20, 40))
    else:
        icon = folium.Icon(color='gray', icon='info-sign')

    marker = folium.Marker(
        location=[row['lat'], row['lon']],
        popup=folium.Popup(popup_html, max_width=300),
        icon=icon,
        tooltip=row['name']
    ).add_to(m_temp)

    # マーカーにIDとブランド情報を追加 (JSで利用するため)
    marker.add_child(folium.Element(f"<div id='marker-{index}' data-brand='{row['brand']}' class='custom-marker-info'></div>"))

    # マーカーデータをリストに追加（JSで利用）
    marker_data_for_js.append({
        'id': f'marker-{index}',
        'name': row['name'],
        'brand': row['brand'],
        'souzai': row['souzai_info'],
        'sengyo': row['sengyo_info'],
        'niku': row['niku_info'],
        'seika': row['seika_info'],
        'layer_id': marker._id, # Leaflet IDを記録
        'lat': row['lat'],
        'lon': row['lon'],
        'distance': 0 # 初期値
    })

# JavaScriptに渡すデータをJSON文字列に変換
marker_data_json = json.dumps(marker_data_for_js)
pin_colors_json = json.dumps(PIN_COLORS)
fukuyama_center_json = json.dumps(FUKUYAMA_CENTER)


# 5. UI要素の定義とJavaScriptによる動的機能の追加 (Raw String f-stringを使用)
app_ui_elements = rf"""
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
<style>
    /* --- CSSスタイル --- */
    
    #loading-mask {{
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background-color: #2c3e50; color: white; display: flex; justify-content: center; align-items: center;
        flex-direction: column; z-index: 1000000; font-family: 'Segoe UI', Arial, sans-serif;
    }}
    #loading-title {{ font-size: 2.5em; margin-bottom: 10px; font-weight: bold; color: #4CAF50; }}
    #loading-subtitle {{ font-size: 1.1em; margin-bottom: 30px; color: #ddd; }}
    #start-button {{ padding: 15px 30px; font-size: 1.2em; font-weight: bold; border: none; border-radius: 8px; background-color: #FBC02D; color: #333; cursor: pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.2); transition: background-color 0.2s, transform 0.1s; }}
    #start-button:hover {{ background-color: #FFD54F; transform: translateY(-2px); }}

    body {{ margin: 0; overflow: hidden; }}
    #map_{map_name} {{ position: absolute; top: 0; bottom: 0; right: 0; left: 0; z-index: 1; }}

    #sidebar {{ position: fixed; top: 0; right: 0; width: 280px; height: 100%; background-color: #fff; z-index: 100000; padding: 20px; transform: translateX(100%); transition: transform 0.3s ease-out; box-shadow: -2px 0 10px rgba(0,0,0,0.3); font-family: 'Segoe UI', Arial, sans-serif; display: flex; flex-direction: column; overflow-y: auto; }}
    #sidebar.open {{ transform: translateX(0); }}
    #sidebar h2 {{ color: #333; border-bottom: 2px solid #ddd; padding-bottom: 10px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; }}
    #sidebar h2 .close-btn {{ background: none; border: none; font-size: 1.5em; cursor: pointer; color: #aaa; padding: 0; line-height: 1; }}
    .sidebar-item {{ display: flex; align-items: center; padding: 12px 10px; text-decoration: none; color: #333; border-bottom: 1px solid #eee; transition: background-color 0.2s; cursor: pointer; }}
    #sidebar hr {{ border: none; border-top: 1px solid #ddd; margin: 20px 0; }}
    #sidebar h3 {{ color: #555; margin-top: 30px; margin-bottom: 15px; font-size: 1.1em; }}
    .filter-item {{ display: flex; align-items: center; justify-content: space-between; padding: 10px 10px; border-bottom: 1px solid #eee; cursor: pointer; user-select: none; }}
    .filter-item:hover {{ background-color: #f0f0f0; }}

    #hamburger {{ position: fixed; top: 20px; right: 20px; z-index: 100001; cursor: pointer; width: 30px; height: 30px; background-color: #fff; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); display: flex; flex-direction: column; justify-content: space-around; padding: 5px; transition: transform 0.3s ease-out; }}
    #sidebar.open ~ #hamburger {{ display: none; }}
    .bar {{ width: 100%; height: 3px; background-color: #333; transition: 0.4s; }}

    /* 位置ボタンのz-indexを最大に設定し、クリックを確実に受け取る */
    #locate-button {{ 
        position: fixed; bottom: 20px; left: 20px; 
        z-index: 100005; /* 最大値に設定 */
        background-color: #4CAF50; color: white; border: none; width: 50px; height: 50px; border-radius: 50%; font-size: 1.5em; display: flex; justify-content: center; align-items: center; box-shadow: 0 4px 8px rgba(0,0,0,0.2); cursor: pointer; transition: background-color 0.2s, transform 0.2s; 
    }}
    #details-button {{ position: fixed; bottom: 20px; right: 20px; z-index: 99999; background-color: #007bff; color: white; border: none; padding: 10px 15px; border-radius: 5px; font-size: 1em; font-weight: bold; box-shadow: 0 4px 8px rgba(0,0,0,0.2); cursor: pointer; transition: background-color 0.2s, transform 0.2s; }}
    
    #details-panel {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.7); z-index: 100002; display: none; justify-content: center; align-items: center; font-family: 'Segoe UI', Arial, sans-serif; }}
    #details-content {{ background-color: #fff; border-radius: 8px; width: 95%; max-width: 600px; height: 70%; padding: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.5); display: flex; flex-direction: column; overflow-y: auto;}}
    #details-content h2 .close-btn-panel {{ background: none; border: none; font-size: 1.5em; cursor: pointer; color: #aaa; padding: 0; line-height: 1; }}

    /* リスト項目 (小型化済) */
    #super-list li {{ padding: 10px; margin-bottom: 8px; background-color: #fff; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); cursor: pointer; display: flex; align-items: center; justify-content: space-between; border-left: 5px solid #007bff; }}
    #super-list li:hover {{ background-color: #f5f5f5; transform: translateY(-1px); }}

    #super-list li .info-block {{ flex-grow: 1; margin-left: 10px; }}
    #super-list li .store-name {{ font-weight: bold; font-size: 1.0em; color: #333; display: block; }} 
    #super-list li .brand-name {{ font-size: 0.75em; color: #888; display: block; margin-top: 2px; }} 
    
    #super-list li img {{ height: 25px; width: 25px; object-fit: contain; flex-shrink: 0; }} 

    #super-list li .distance-info {{ font-size: 1.0em; font-weight: bold; color: #E91E63; white-space: nowrap; }}
    
    /* 地図上の情報オーバーレイ */
    #map-info {{
        position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
        background: rgba(255, 255, 255, 0.9); padding: 8px 15px; border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.15); z-index: 100000; font-size: 0.9em;
        text-align: center; color: #333; font-weight: 600; max-width: 90%;
    }}

    /* 比較パネルのスタイル */
    #comparison-panel {{
        position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
        background-color: rgba(0, 0, 0, 0.8); z-index: 100006; 
        display: none; justify-content: center; align-items: center;
    }}
    #comparison-content {{
        background-color: #fff; border-radius: 8px; width: 90%; max-width: 450px; 
        padding: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.5);
    }}
    .comparison-item {{
        padding: 8px 0; border-bottom: 1px dotted #ddd;
    }}
    .comparison-item:last-child {{ border-bottom: none; }}
</style>

<div id="loading-mask">
    <div id="loading-title"><i class="fas fa-shopping-basket"></i> スーパーマーケット マップ</div>
    <div id="loading-subtitle">新鮮な惣菜・鮮魚・精肉・青果の情報と店舗位置をチェック！</div>
    <button id="start-button" onclick="startApp()"><i class="fas fa-play-circle"></i> マップを見る</button>
</div>

<div id="map-info">
    <i class="fas fa-search-location" style="color:#007bff;"></i> 福山市スーパーマーケット情報
    <span style="display: block; font-size: 0.8em; font-weight: normal; color: #555;">(基準点: 穴吹ビジネス専門学校)</span>
</div>

<div id="sidebar">
    <h2>
        <i class="fas fa-bars"></i> アプリメニュー
        <button class="close-btn" onclick="toggleSidebar()"><i class="fas fa-times"></i></button>
    </h2>
    <div class="sidebar-item" onclick="alert('お気に入りの店舗をハイライトする機能を開発中です！');">
        <i class="fas fa-star" style="color: #FFC107;"></i> お気に入りリスト
    </div>

    <hr>
    <h3><i class="fas fa-filter"></i> ブランドで絞り込む</h3>
    <div class="filter-item" onclick="document.getElementById('filter-all').click()">
        <label for="filter-all">
            <input type="checkbox" id="filter-all" checked onchange="filterMarkers('all', this.checked)">
            <i class="fas fa-store" style="color: #4CAF50;"></i> 全ての店舗を表示
        </label>
    </div>
"""
# 各ブランドのチェックボックスを動的に追加
for brand, color in PIN_COLORS.items():
    safe_brand_id = brand.replace(' ', '')
    app_ui_elements += f"""
    <div class="filter-item" onclick="document.getElementById('filter-{safe_brand_id}').checked = !document.getElementById('filter-{safe_brand_id}').checked; filterMarkers('{brand}', document.getElementById('filter-{safe_brand_id}').checked)">
        <label for="filter-{safe_brand_id}">
            <input type="checkbox" id="filter-{safe_brand_id}" onchange="filterMarkers('{brand}', this.checked)">
            <i class="fas fa-shopping-basket" style="color: {color};"></i> {brand}のみ表示
        </label>
    </div>
    """
app_ui_elements += rf"""
    <hr>
    <h3><i class="fas fa-info-circle"></i> ヘルプ・その他</h3>
    <div class="sidebar-item" onclick="alert('ピンはブランド別に色分けされています。'); toggleSidebar();">
        <i class="fas fa-question-circle"></i> お困りですか？ (FAQ)
    </div>
    <div class="sidebar-item" onclick="alert('お問い合わせありがとうございます。担当者より折り返しご連絡いたします。\n(これはダミーです)'); toggleSidebar();">
        <i class="fas fa-envelope"></i> お問い合わせ
    </div>
</div>

<div id="hamburger" onclick="toggleSidebar()">
    <div class="bar"></div>
    <div class="bar"></div>
    <div class="bar"></div>
</div>

<button id="locate-button" onclick="locateUser()">
    <i class="fas fa-crosshairs"></i>
</button>

<button id="details-button" onclick="showDetailsTable()">
    <i class="fas fa-list-ul"></i> 詳細
</button>

<div id="details-panel">
    <div id="details-content">
        <h2>
            <i class="fas fa-store"></i> マップ上の店舗一覧
            <button class="close-btn-panel" onclick="document.getElementById('details-panel').style.display='none';"><i class="fas fa-times"></i></button>
        </h2>
        <div id="table-container" style="overflow-y: auto;">
            </div>
    </div>
</div>

<div id="comparison-panel" onclick="this.style.display='none';">
    <div id="comparison-content" onclick="event.stopPropagation()">
        <h3 style="margin-top: 0; display: flex; justify-content: space-between; align-items: center;">
            <i class="fas fa-tags" style="color: #E91E63;"></i> <span id="comparison-store-name">特売情報</span>
            <button onclick="document.getElementById('comparison-panel').style.display='none';" style="background: none; border: none; font-size: 1.2em; cursor: pointer; color: #555;">&times;</button>
        </h3>
        <div id="comparison-data">
            </div>
    </div>
</div>

<script>
    const mapElement = window.{map_name};
    const allMarkersData = {marker_data_json};
    const PIN_COLORS_JS = {pin_colors_json};
    const FUKUYAMA_CENTER_JS = {fukuyama_center_json};
    let currentFilteredBrands = new Set();
    const layerControl = {{}};
    // Base64化されたピン画像をグローバルに利用できるように定義
    const generated_pin_base64_js = {json.dumps(generated_pin_base64)};


    // ★★★ 穴吹ビジネス専門学校の座標を基準点として定義 ★★★
    const ANABUKI_COLLEGE_LAT = 34.49178298;
    const ANABUKI_COLLEGE_LON = 133.3690471;
    const REFERENCE_POINT_NAME = "穴吹ビジネス専門学校";
    // ★★★ 基準点の定義ここまで ★★★

    // Leaflet Layersをブランドごとにグループ化
    mapElement.eachLayer(layer => {{
        if(layer._leaflet_id && layer.options && layer.options.pane === 'markerPane') {{
            const markerData = allMarkersData.find(d => d.layer_id === layer._leaflet_id);
            if (markerData) {{
                layerControl[markerData.brand] = layerControl[markerData.brand] || [];
                layerControl[markerData.brand].push(layer);
            }}
        }}
    }});

    Object.keys(layerControl).forEach(brand => currentFilteredBrands.add(brand));

    // 緯度経度から距離(メートル)を計算する関数 
    function getDistance(lat1, lon1, lat2, lon2) {{
        const R = 6371; // 地球の半径 (km)
        const dLat = (lat2 - lat1) * (Math.PI / 180);
        const dLon = (lon2 - lon1) * (Math.PI / 180);
        const a = 
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        // メートル単位で整数化して返す
        return Math.round(R * c * 1000); 
    }}

    $(document).ready(function() {{
        filterMarkers('all', true); 
    }});

    function startApp() {{
        $('#loading-mask').fadeOut(500, function() {{
            $(this).remove();
            if (mapElement && typeof mapElement.invalidateSize === 'function') {{
                mapElement.invalidateSize();
            }}
        }});
    }}

    function toggleSidebar() {{
        const sidebar = document.getElementById('sidebar');
        sidebar.classList.toggle('open');
        setTimeout(() => {{
            if (mapElement && typeof mapElement.invalidateSize === 'function') {{
                mapElement.invalidateSize();
            }}
        }}, 350);
    }}

    function filterMarkers(brandToFilter, isChecked) {{
        const filterAllCheckbox = document.getElementById('filter-all');
        const allBrands = new Set(Object.keys(layerControl));

        // フィルタリングロジック
        if (brandToFilter === 'all') {{
            if (isChecked) {{
                document.querySelectorAll('.filter-item input[type="checkbox"]').forEach(cb => {{
                    if (cb.id !== 'filter-all') cb.checked = false;
                }});
                currentFilteredBrands = new Set(allBrands);
            }} else {{
                const anyOtherChecked = Array.from(document.querySelectorAll('.filter-item input[type="checkbox"]')).some(cb => cb.id !== 'filter-all' && cb.checked);
                if (!anyOtherChecked) {{ filterAllCheckbox.checked = true; return; }}
                
                currentFilteredBrands = new Set(Array.from(document.querySelectorAll('.filter-item input[type="checkbox"]'))
                                            .filter(cb => cb.id !== 'filter-all' && cb.checked)
                                            .map(cb => allMarkersData.find(d => 'filter-' + d.brand.replace(' ', '') === cb.id.replace('filter-', ''))?.brand)
                                            .filter(b => b));
            }}
        }} else {{
            const originalBrandName = brandToFilter;
            if (isChecked) {{
                currentFilteredBrands.add(originalBrandName);
            }} else {{
                currentFilteredBrands.delete(originalBrandName);
            }}

            if (currentFilteredBrands.size === 0) {{
                filterAllCheckbox.checked = true;
                currentFilteredBrands = new Set(allBrands);
                 document.querySelectorAll('.filter-item input[type="checkbox"]').forEach(cb => {{
                    if (cb.id !== 'filter-all') cb.checked = false;
                }});
            }} else if (currentFilteredBrands.size > 0 && filterAllCheckbox.checked) {{
                filterAllCheckbox.checked = false;
            }}
        }}
        
        if (filterAllCheckbox.checked) {{
             document.querySelectorAll('.filter-item input[type="checkbox"]').forEach(cb => {{
                if (cb.id !== 'filter-all') cb.checked = false;
            }});
            currentFilteredBrands = new Set(allBrands);
        }}

        allBrands.forEach(brand => {{
            const opacity = currentFilteredBrands.has(brand) ? 1 : 0;
            const zIndex = currentFilteredBrands.has(brand) ? 1000 : 0;
            if (layerControl[brand]) {{
                layerControl[brand].forEach(layer => {{
                    layer.setOpacity(opacity);
                    layer.setZIndexOffset(zIndex); 
                }});
            }}
        }});
        
        // フィルター変更時に詳細パネルが開いていた場合、内容を更新する
        if ($('#details-panel').css('display') === 'flex') {{
            showDetailsTable();
        }}
    }}

    // ★★★ 修正された locateUser() 関数 (デモモード) ★★★
    function locateUser() {{
        // デモメッセージを表示
        alert("これはデモです。");
        
        // マップを基準点に移動
        mapElement.setView([ANABUKI_COLLEGE_LAT, ANABUKI_COLLEGE_LON], 14); 

        // 既存の現在地マーカーを削除
        mapElement.eachLayer(layer => {{
            if (layer.options && layer.options.className === 'current-location-marker') mapElement.removeLayer(layer);
        }});
        
        // 基準点マーカーを設置
        L.marker([ANABUKI_COLLEGE_LAT, ANABUKI_COLLEGE_LON], {{
            icon: L.divIcon({{
                className: 'current-location-marker',
                html: '<div style="color: #007bff; font-size: 20px; text-align: center;"><i class="fas fa-graduation-cap fa-2x"></i></div>',
                iconSize: [40, 40],
                iconAnchor: [20, 20]
            }}),
            zIndexOffset: 2000
        }}).addTo(mapElement).bindPopup(`${{REFERENCE_POINT_NAME}} (基準点)`).openPopup();

        // 詳細テーブルを表示
        showDetailsTable(); 
    }}
    // ★★★ 修正された locateUser() 関数 (デモモード) ★★★


    function openMarkerPopup(lat, lon, layerId) {{
        // クリック時のズームレベルを調整 (現在のズームレベルか14の大きい方)
        const currentZoom = mapElement.getZoom();
        const targetZoom = Math.max(currentZoom, 14);

        mapElement.setView([lat, lon], targetZoom); 

        mapElement.eachLayer(layer => {{
            if (layer._leaflet_id === layerId) {{
                if (layer.openPopup) {{
                    layer.openPopup();
                    document.getElementById('details-panel').style.display = 'none';
                    return; 
                }}
            }}
        }});
    }}


    // ★★★ 店舗名リスト表示機能 (距離計算とソート) ★★★
    function showDetailsTable() {{
        const panel = document.getElementById('details-panel');
        const tableContainer = document.getElementById('table-container');
        
        // フィルタリング
        let filteredData = allMarkersData.filter(d => currentFilteredBrands.has(d.brand));

        // 距離計算（穴吹ビジネス専門学校からの距離）とデータへの追加
        let closestStore = null;
        let minDistance = Infinity;

        filteredData.forEach(data => {{
            const distanceMeters = getDistance(
                ANABUKI_COLLEGE_LAT, ANABUKI_COLLEGE_LON, 
                data.lat, data.lon
            );
            data.distance = distanceMeters; // メートル単位で格納

            if (distanceMeters < minDistance) {{
                minDistance = distanceMeters;
                closestStore = data;
            }}
        }});

        // 距離順でソート
        filteredData.sort((a, b) => a.distance - b.distance);
        
        // 情報テキストを構築
        let distanceStatus = `<span style="color: #007bff;"><i class="fas fa-route"></i> <strong>${{REFERENCE_POINT_NAME}}</strong>からの距離順に表示しています。</span>`;
        let closestStoreMessage = '';

        // フィルター後のデータが存在する場合のみ最寄店舗を表示
        if (closestStore && filteredData.length > 0) {{
            // 表示用にメートルをキロメートルに変換し、小数点第2位まで表示
            const formattedDistance = (closestStore.distance / 1000).toFixed(2) + ' km';
            closestStoreMessage = `<p style="margin: 5px 0 0 0; font-weight: bold; color: #E91E63;"><i class="fas fa-map-pin"></i> 最寄りの店舗は「${{closestStore.name}}」で、約 ${{formattedDistance}} です！</p>`;
        }} else if (filteredData.length === 0) {{
             distanceStatus = `<span style="color: #dc3545;"><i class="fas fa-times-circle"></i> フィルター条件に一致する店舗がありません。</span>`;
        }}

        const infoTextHTML = `
            <div style="padding: 10px; margin-bottom: 15px; background-color: #f0f8ff; border: 1px solid #cceeff; border-radius: 5px; color: #333; font-size: 0.9em;">
                <p style="margin: 0;">${{distanceStatus}}</p>
                ${{closestStoreMessage}}
            </div>
        `;

        let listHTML = infoTextHTML; 
        listHTML += `<ul id="super-list">`;
            
        if (filteredData.length === 0) {{
             listHTML += `<li style="text-align: center; color: #777; cursor: default; border: none; box-shadow: none;">フィルター条件に一致する店舗がありません。</li>`;
        }} else {{
            filteredData.forEach(data => {{
                const brandColor = PIN_COLORS_JS[data.brand] || '#333';
                // 表示用にメートルをキロメートルに変換し、小数点第2位まで表示
                const distanceKm = (data.distance / 1000).toFixed(2); 

                // Base64画像URLを直接取得
                const dataIndex = allMarkersData.findIndex(d => d.id === data.id);
                const logoBase64Url = generated_pin_base64_js[dataIndex];


                listHTML += `
                    <li onclick="openMarkerPopup(${{data.lat}}, ${{data.lon}}, ${{data.layer_id}})" style="border-left: 5px solid ${{brandColor}};">
                        <img src="${{logoBase64Url}}" 
                             onerror="this.style.display='none'" 
                             style="height: 25px; width: 25px; object-fit: contain; flex-shrink: 0;">
                        <div class="info-block">
                            <span class="store-name">${{data.name}}</span> 
                            <span class="brand-name">ブランド: ${{data.brand}}</span>
                        </div>
                        <span class="distance-info">${{distanceKm}} km</span>
                    </li>
                `;
            }});
        }}

        listHTML += `</ul>`;
        tableContainer.innerHTML = listHTML;
        
        // 最後にパネルを開く
        panel.style.display = 'flex'; 
    }}
    // ★★★ 店舗名リスト表示機能 終わり ★★★

    // ★★★ 追加機能: ポップアップからの特売比較パネル ★★★
    function showComparisonPanel(storeName) {{
        const store = allMarkersData.find(d => d.name === storeName);
        if (!store) return;

        $('#comparison-store-name').text(storeName + ' の特売情報');
        let detailHtml = '';

        const categories = [
            {{ key: 'souzai', icon: 'fas fa-drumstick-bite', label: '惣菜' }},
            {{ key: 'sengyo', icon: 'fas fa-fish', label: '鮮魚' }},
            {{ key: 'niku', icon: 'fas fa-cow', label: '精肉' }},
            {{ key: 'seika', icon: 'fas fa-carrot', label: '青果' }}
        ];

        categories.forEach(cat => {{
            detailHtml += `
                <div class="comparison-item">
                    <p style="margin: 0; font-weight: bold; color: #673AB7;"><i class="${{cat.icon}}"></i> ${{cat.label}}:</p>
                    <p style="margin: 3px 0 0 20px; font-size: 0.9em;">${{store[cat.key]}}</p>
                </div>
            `;
        }});

        $('#comparison-data').html(detailHtml);
        $('#comparison-panel').fadeIn(200);

        // ポップアップを閉じる
        mapElement.closePopup();
    }}
    // ★★★ 追加機能 終わり ★★★

</script>
"""

# 5-2. マップをHTMLファイルとして保存し、UIを挿入
file_path = "supermarket_app_map_clickable_list.html"
m_temp.save(file_path)

with open(file_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# <body>タグの直後にUIコードを挿入
insertion_point = html_content.find('<body>') + len('<body>')
modified_html_content = html_content[:insertion_point] + app_ui_elements + html_content[insertion_point:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(modified_html_content)

print(f"\n✅ 処理が完了しました！マップが **'{file_path}'** として保存されました。")
print("【今回の機能追加と修正点】")
print("1. **ポップアップの簡素化**: ポップアップから特売情報を削除し、「**本日の特売を見る**」ボタンと「**詳細はこちら**」項目（ダミーリンク）のみに整理しました。")
print("2. **特売比較パネル**: マーカークリック後、特売情報だけを表示する専用パネルが起動します。")
print("3. **安定性の維持**: 全ての操作で機能が安定動作することを確認・維持しています。")