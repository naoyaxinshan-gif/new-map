"""
スーパーマーケット地図アプリケーション生成スクリプト

福山市内のスーパーマーケット店舗情報を地図上に表示し、
インタラクティブなWebアプリケーションを生成します。
"""
import pandas as pd
import folium
from PIL import Image, ImageDraw, ImageFont
import os
import base64
from io import BytesIO
import json
import logging
import webview
from typing import Dict, List, Optional, Tuple
import math

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

# ============================================================================
# 定数定義
# ============================================================================

# ファイル・フォルダ設定
LOGO_FOLDER = 'logos'
PIN_BASE_IMAGE = 'pin_base.png'
OUTPUT_HTML_FILE = "supermarket_app_map_clickable_list.html"

# 地図設定
FUKUYAMA_CENTER = [34.50, 133.37]
MAP_NAME = "m_temp"
MAP_ZOOM_START = 12

# 画像設定
LOGO_SIZE = (60, 60)
PIN_SIZE = (100, 100)
ICON_SIZE = (40, 40)
ICON_ANCHOR = (20, 40)

# 基準点設定
INITIAL_REFERENCE_LAT = 34.49178298
INITIAL_REFERENCE_LON = 133.3690471
INITIAL_REFERENCE_NAME = "穴吹ビジネス専門学校"
DEMO_LOCATION_LAT = 34.485
DEMO_LOCATION_LON = 133.365
DEMO_REFERENCE_NAME = "デモ現在地 (ボタン)"

# 企業取引認証キー（開発者と企業間で共有）
BUSINESS_ACCESS_KEY = "BUSINESS2024KEY"

# ブランドカラー設定
PIN_COLORS: Dict[str, str] = {
    'ハローズ': '#FBC02D',
    'エブリイ': '#00BCD4',
    'フレスタ': '#673AB7',
    'フジ': '#9C27B0',
    'ラ・ムー': '#E91E63',
    '業務スーパー': '#388E3C',
    'ディオ': '#2196F3',
    'オンリーワン': '#FF9800',
    'ゆめタウン': '#E53935',
    'ザ・ビッグ': '#8D6E63',
    'ミスターマックス': '#546E7A',
    'なかやま牧場': '#795548',
    'マルナカ': '#4CAF50',
    'Ａ−プライス': '#00BFA5',
    'ニチエー': '#D32F2F',
    '生鮮食品 おだ': '#FF5722',
}

# デフォルト値
DEFAULT_PIN_COLOR = '#CCCCCC'
DEFAULT_WEBSITE = 'https://fukuyama-super-info.com/'
DEFAULT_INFO_TEMPLATE = '{brand}: 本日の特売情報は店頭にて！ (ダミー情報)'

# フォント設定
FONT_PATHS = {
    'windows': "C:/Windows/Fonts/meiryo.ttc",
    'linux': "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
}
FONT_SIZE = 30

# ============================================================================
# データ定義
# ============================================================================

# 既存データ
EXISTING_DATA = {
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
        'logo_ハローズ.png', 'logo_ハローズ.png', 'logo_ハローズ.png', 'logo_エブリイ.png',
        'logo_エブリイ.png', 'logo_ハローズ.png', 'logo_フレスタ.png', 'logo_フジ.png',
        'logo_ハローズ.png', 'logo_フレスタ.png', 'logo_ラ・ムー.png', 'logo_ハローズ.png',
        'logo_ハローズ.png'
    ],
    'website': [
        'https://www.halows.com/', 'https://www.halows.com/', 'https://www.halows.com/', 'https://www.super-every.co.jp/',
        'https://www.super-every.co.jp/', 'https://www.halows.com/', 'https://www.fresta.co.jp/', 'https://www.the-fuji.com/',
        'https://www.halows.com/', 'https://www.fresta.co.jp/', 'https://www.e-dkt.co.jp/',
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

# 追加データ
NEW_DATA = {
    'name': [
        'ハローズ 神辺店', 'ハローズ 戸手店', 'ハローズ 春日店', 'ハローズ 引野店', 'ハローズ 東福山店',
        'ハローズ 手城店', 'ハローズ 水呑店', 'ハローズ 南松永店', 'ハローズ 沼南店',
        'エブリイ 松永店', 'エブリイ瀬戸店', 'エブリイ御幸店', 'エブリイ神辺店', 'エブリイ本庄店',
        'エブリイ蔵王店', 'エブリイ川口店', 'エブリイ伊勢丘店',
        'フレスタ 福山三吉店', 'フレスタ 北吉津店', 'フレスタ 草戸店', 'フレスタ 多治米店',
        '業務スーパー新市店', 'ラ・ムー 松永店', 'ラ・ムー 手城店', 'ディオ 福山南店',
        'フジグラン神辺 食品館', 'オンリーワン 駅家店', 'オンリーワン 千田店', 'オンリーワン 旭ヶ丘店',
        'オンリーワン 木之庄店', 'オンリーワン 山手店', 'オンリーワン 瀬戸店',
        'ゆめタウン 蔵王', 'ゆめタウン福山', 'ザ・ビッグ 神辺店', 'ザ・ビッグ大門店',
        'ミスターマックス新神辺店',
        'なかやま牧場 ハート新徳田店', 'なかやま牧場 ハート加茂店', 'なかやま牧場［ﾊｰﾄ坪生店］', 'なかやま牧場 引野店',
        'なかやま牧場 ハート木之庄店', 'なかやま牧場 ハート新涯店',
        'マルナカ 加茂店', 'Ａ−プライス 福山店',
        'ニチエー 柳津店', 'ニチエー さんらいず店', 'ニチエー 瀬戸店', 'ニチエー 沼南店',
        '生鮮食品 おだ 春日店'
    ],
    'lat': [
        34.549238, 34.549010, 34.511183, 34.500121, 34.490001,
        34.484085, 34.446823, 34.443160, 34.387728,
        34.442332, 34.475457, 34.540975, 34.547862, 34.486838,
        34.503659, 34.468972, 34.504264,
        34.495523, 34.497068, 34.478892, 34.468429,
        34.545228, 34.446731, 34.483819, 34.465147,
        34.545245, 34.549297, 34.518545, 34.492134,
        34.496204, 34.494895, 34.471791,
        34.504926, 34.487064, 34.557168, 34.494797,
        34.540661,
        34.548747, 34.568176, 34.527446, 34.496260,
        34.498596, 34.454583,
        34.560882, 34.494565,
        34.439995, 34.453543, 34.473304, 34.386952,
        34.510628
    ],
    'lon': [
        133.377984, 133.283165, 133.415063, 133.406021, 133.410593,
        133.392729, 133.386847, 133.254940, 133.323727,
        133.251304, 133.317128, 133.348727, 133.382452, 133.350845,
        133.394152, 133.383982, 133.423391,
        133.378392, 133.365369, 133.360637, 133.370928,
        133.293464, 133.243272, 133.398270, 133.383363,
        133.357068, 133.326900, 133.365520, 133.422231,
        133.353517, 133.337047, 133.314893,
        133.400447, 133.378583, 133.389616, 133.438232,
        133.362873,
        133.371937, 133.346001, 133.439373, 133.400904,
        133.354959, 133.393429,
        133.347027, 133.397965,
        133.263470, 133.256207, 133.314423, 133.324780,
        133.413331
    ],
    'brand': [
        'ハローズ', 'ハローズ', 'ハローズ', 'ハローズ', 'ハローズ',
        'ハローズ', 'ハローズ', 'ハローズ', 'ハローズ',
        'エブリイ', 'エブリイ', 'エブリイ', 'エブリイ', 'エブリイ',
        'エブリイ', 'エブリイ', 'エブリイ',
        'フレスタ', 'フレスタ', 'フレスタ', 'フレスタ',
        '業務スーパー', 'ラ・ムー', 'ラ・ムー', 'ディオ',
        'フジ', 'オンリーワン', 'オンリーワン', 'オンリーワン',
        'オンリーワン', 'オンリーワン', 'オンリーワン',
        'ゆめタウン', 'ゆめタウン', 'ザ・ビッグ', 'ザ・ビッグ',
        'ミスターマックス',
        'なかやま牧場', 'なかやま牧場', 'なかやま牧場', 'なかやま牧場',
        'なかやま牧場', 'なかやま牧場',
        'マルナカ', 'Ａ−プライス',
        'ニチエー', 'ニチエー', 'ニチエー', 'ニチエー',
        '生鮮食品 おだ'
    ]
}

# ============================================================================
# データ処理関数
# ============================================================================

def normalize_brand_name(brand: str) -> str:
    """
    ブランド名を正規化する（ファイル名などに使用）
    
    Args:
        brand: ブランド名
        
    Returns:
        正規化されたブランド名
    """
    return brand.lower().replace(' ', '').replace('［', '').replace('］', '').replace('−', '')


def fill_info(brand: str, data_key: str) -> str:
    """
    追加データに不足している情報を既存データから補完する
    
    Args:
        brand: ブランド名
        data_key: 補完するデータのキー
        
    Returns:
        補完された情報
    """
    existing_brand_indices = [
        i for i, b in enumerate(EXISTING_DATA['brand']) if b == brand
    ]
    safe_brand_name = normalize_brand_name(brand)
    
    if data_key == 'logo_file':
        if existing_brand_indices:
            return EXISTING_DATA['logo_file'][existing_brand_indices[0]]
        return f"logo_{safe_brand_name}.png"
            
    if data_key == 'website':
        return DEFAULT_WEBSITE
        
    if existing_brand_indices:
        return EXISTING_DATA[data_key][existing_brand_indices[0]]
        
    return DEFAULT_INFO_TEMPLATE.format(brand=brand)


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    2点間の距離を計算（Haversine formula）
    
    Args:
        lat1, lon1: 第1点の緯度・経度
        lat2, lon2: 第2点の緯度・経度
        
    Returns:
        距離（メートル）
    """
    R = 6371  # 地球の半径（km）
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2 +
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
        math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c * 1000  # メートルに変換


def prepare_data() -> pd.DataFrame:
    """
    既存データと追加データを結合してDataFrameを作成
    
    Returns:
        結合された店舗データのDataFrame
    """
    # 追加データにロゴファイルと情報を補完
    info_keys = ['logo_file', 'website', 'souzai_info', 'sengyo_info', 'niku_info', 'seika_info']
    for data_key in info_keys:
        NEW_DATA[data_key] = [
            fill_info(brand, data_key) for brand in NEW_DATA['brand']
        ]
    
    # データの結合
    df = pd.concat(
        [pd.DataFrame(EXISTING_DATA), pd.DataFrame(NEW_DATA)],
        ignore_index=True
    )
    return df


# データの準備
df = prepare_data()

# 穴吹ビジネス専門学校から各店舗までの距離を事前計算
df['distance_from_reference'] = df.apply(
    lambda row: calculate_distance(
        INITIAL_REFERENCE_LAT, INITIAL_REFERENCE_LON,
        row['lat'], row['lon']
    ),
    axis=1
)

# ============================================================================
# ファイル・フォルダ準備
# ============================================================================

os.makedirs(LOGO_FOLDER, exist_ok=True)

# ============================================================================
# 画像生成関数
# ============================================================================

def create_pin_base_image() -> None:
    """
    PIN_BASE_IMAGEが存在しない場合、代替ピンベース画像を生成
    """
    if os.path.exists(PIN_BASE_IMAGE):
        return
        
    logger.info(f"'{PIN_BASE_IMAGE}' が見つかりませんでした。代替ピンベース画像を生成します。")
    try:
        img = Image.new('RGBA', PIN_SIZE, (0, 0, 0, 0))
        ImageDraw.Draw(img).ellipse(
            (0, 0, PIN_SIZE[0] - 1, PIN_SIZE[1] - 1),
            fill=DEFAULT_PIN_COLOR
        )
        img.save(PIN_BASE_IMAGE)
    except Exception as e:
        logger.error(f"ピンベース画像の生成に失敗しました: {e}")


def get_font_path() -> Optional[str]:
    """
    システムに応じたフォントパスを取得
    
    Returns:
        フォントパス、取得できない場合はNone
    """
    if os.name == 'nt':
        font_path = FONT_PATHS['windows']
    else:
        font_path = FONT_PATHS['linux']
    
    if os.path.exists(font_path):
        return font_path
    return None


def create_placeholder_logo(brand_name: str, size: Tuple[int, int] = LOGO_SIZE) -> None:
    """
    ブランド名の頭文字を中央に配置した代替ロゴ画像を生成
    
    Args:
        brand_name: ブランド名
        size: ロゴサイズ（デフォルト: LOGO_SIZE）
    """
    try:
        logo_filename = df[df['brand'] == brand_name]['logo_file'].iloc[0]
        logo_path = os.path.join(LOGO_FOLDER, logo_filename)
        
        if os.path.exists(logo_path):
            return

        logger.warning(
            f"ロゴファイル '{logo_filename}' が見つかりませんでした。"
            f"代替画像を生成します。"
        )

        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        pin_color = PIN_COLORS.get(brand_name, DEFAULT_PIN_COLOR)
        draw.ellipse((0, 0, size[0], size[1]), fill=pin_color)
        
        initial = brand_name[0]
        
        # フォントの読み込み
        font = ImageFont.load_default()
        font_path = get_font_path()
        if font_path:
            try:
                font = ImageFont.truetype(font_path, FONT_SIZE)
            except Exception:
                logger.warning(f"フォント '{font_path}' の読み込みに失敗しました。デフォルトフォントを使用します。")
        
        fill_color = "#FFFFFF"
        
        # テキストの中央配置
        if hasattr(draw, 'textbbox'):
            text_bbox = draw.textbbox((0, 0), initial, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            x = (size[0] - text_width) // 2
            y = (size[1] - text_height) // 2
            draw.text((x, y), initial, font=font, fill=fill_color)
        else:
            draw.text(
                (size[0] // 4, size[1] // 4),
                initial,
                fill=fill_color,
                font=font
            )

        img.save(logo_path)
        logger.info(f"代替ロゴを生成しました: {logo_path}")
        
    except Exception as e:
        logger.error(f"代替ロゴファイルの生成に失敗しました (ブランド: {brand_name}): {e}")


def prepare_images() -> None:
    """
    必要な画像ファイルを準備（ピンベースとロゴプレースホルダー）
    """
    create_pin_base_image()
    for brand in df['brand'].unique():
        create_placeholder_logo(brand)


# 画像の準備
prepare_images()


# ============================================================================
# ピン画像生成関数
# ============================================================================

def create_logo_pin_base64(
    logo_path: str,
    pin_base_path: str,
    pin_color: str = DEFAULT_PIN_COLOR,
    logo_size: Tuple[int, int] = LOGO_SIZE
) -> Optional[str]:
    """
    ロゴとピンベースを合成してBase64エンコードされた画像を生成
    
    Args:
        logo_path: ロゴ画像のパス
        pin_base_path: ピンベース画像のパス
        pin_color: ピンの色
        logo_size: ロゴサイズ
        
    Returns:
        Base64エンコードされた画像文字列、失敗時はNone
    """
    try:
        pin_base = Image.open(pin_base_path).convert("RGBA").resize(
            PIN_SIZE, Image.LANCZOS
        )
        logo_img = Image.open(logo_path).convert("RGBA").resize(
            logo_size, Image.LANCZOS
        )

        # カラー付きピンシェイプの作成
        colored_background = Image.new('RGBA', pin_base.size, pin_color)
        pin_mask = pin_base.split()[-1]
        colored_pin_shape = Image.new('RGBA', pin_base.size, (0, 0, 0, 0))
        colored_pin_shape.paste(colored_background, (0, 0), pin_mask)

        # ロゴを中央に配置（少し上にオフセット）
        x_offset = (colored_pin_shape.width - logo_img.width) // 2
        y_offset = (colored_pin_shape.height - logo_img.height) // 2 - 10
        final_pin = colored_pin_shape.copy()
        final_pin.paste(logo_img, (x_offset, y_offset), logo_img)

        # Base64エンコード
        buffered = BytesIO()
        final_pin.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
        
    except Exception as e:
        logger.error(f"ピン画像合成中にエラーが発生しました: {e}. 単色ピンを使用します。")
        return create_solid_color_pin(pin_color)


def create_solid_color_pin(pin_color: str) -> Optional[str]:
    """
    単色のピン画像を生成（フォールバック用）
    
    Args:
        pin_color: ピンの色
        
    Returns:
        Base64エンコードされた画像文字列、失敗時はNone
    """
    try:
        img = Image.new('RGBA', PIN_SIZE, (0, 0, 0, 0))
        ImageDraw.Draw(img).ellipse(
            (0, 0, PIN_SIZE[0] - 1, PIN_SIZE[1] - 1),
            fill=pin_color
        )
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    except Exception as e:
        logger.error(f"単色ピン生成に失敗しました: {e}")
        return None


def generate_all_pin_images() -> Dict[int, str]:
    """
    全店舗のピン画像を生成し、Base64として辞書に格納
    
    Returns:
        インデックスをキー、Base64画像URLを値とする辞書
    """
    generated_pin_base64: Dict[int, str] = {}
    for index, row in df.iterrows():
        logo_path = os.path.join(LOGO_FOLDER, row['logo_file'])
        pin_color = PIN_COLORS.get(row['brand'], DEFAULT_PIN_COLOR)
        b64_image = create_logo_pin_base64(logo_path, PIN_BASE_IMAGE, pin_color)
        if b64_image:
            generated_pin_base64[index] = f"data:image/png;base64,{b64_image}"
    return generated_pin_base64


# 全ピン画像の生成
generated_pin_base64 = generate_all_pin_images()


# --- 4. Foliumマップの作成とマーカーの追加 ---
FUKUYAMA_CENTER = [34.50, 133.37]
map_name = "m_temp"
# 地図をクリック可能にするために、folium.Mapのデフォルトのフォールバックレイヤーを設定
m_temp = folium.Map(location=FUKUYAMA_CENTER, zoom_start=12, name=map_name)
marker_data_for_js = []

for index, row in df.iterrows():
    pin_image_base64 = generated_pin_base64.get(index)

    logo_base64_for_popup = generated_pin_base64.get(index, "").replace("data:image/png;base64,", "")
            
    popup_html = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 250px;">
        <h4 style="margin: 0 0 8px 0; color: #333; border-bottom: 2px solid {PIN_COLORS.get(row['brand'], '#ccc')}; padding-bottom: 5px;">
            <img src='data:image/png;base64,{logo_base64_for_popup}' alt='{row['brand']}ロゴ' style='height: 20px; vertical-align: middle; margin-right: 5px; background-color: {PIN_COLORS.get(row['brand'], '#ccc')}; border-radius: 5px;'>
            {row['name']}
        </h4>
        <p style="margin: 5px 0;"><a href="{row['website']}" target="_blank" style="color: #007bff; text-decoration: none;"><i class="fas fa-globe"></i> 公式ウェブサイト</a></p>
        <hr style="margin: 10px 0; border-top: 1px solid #eee;">

        <button onclick="showComparisonPanel('{row['name']}')" style="margin-top: 5px; padding: 8px 10px; background-color: #ffc107; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%; color: #333; transition: background-color 0.2s;">
            <i class="fas fa-search"></i> 本日の特売を見る
        </button>

        <div onclick="showCategorySelector('{row['name']}', '{index}')" style="margin-top: 10px; text-align: center; font-size: 0.9em; color: #007bff; cursor: pointer; padding: 5px 0; border-top: 1px solid #eee; transition: color 0.2s;">
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

    marker.add_child(folium.Element(f"<div id='marker-{index}' data-brand='{row['brand']}' class='custom-marker-info'></div>"))

    marker_data_for_js.append({
        'id': f'marker-{index}',
        'name': row['name'],
        'brand': row['brand'],
        'souzai': row['souzai_info'],
        'sengyo': row['sengyo_info'],
        'niku': row['niku_info'],
        'seika': row['seika_info'],
        'layer_id': marker._id,
        'lat': row['lat'],
        'lon': row['lon'],
        'distance': int(row['distance_from_reference'])  # 事前計算された距離（メートル）
    })

marker_data_json = json.dumps(marker_data_for_js)
pin_colors_json = json.dumps(PIN_COLORS)
fukuyama_center_json = json.dumps(FUKUYAMA_CENTER)


# 5. UI要素の定義とJavaScriptによる動的機能の追加 (Raw String f-stringを使用)
app_ui_elements = rf"""
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
<style>
    /* --- CSSスタイル --- */

    /* ホーム画面/ローディング画面の強化 */
    #loading-mask {{
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        background-size: 200% 200%;
        color: white; display: flex; justify-content: center; align-items: center;
        flex-direction: column; z-index: 1000000; font-family: 'Segoe UI', Arial, sans-serif;
        animation: gradientShift 8s ease infinite, fadeIn 0.8s ease-in-out;
        overflow: hidden;
    }}
    @keyframes gradientShift {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}
    @keyframes fadeIn {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}
    #loading-mask::before {{
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
        background-size: 50px 50px;
        animation: float 20s linear infinite;
    }}
    @keyframes float {{
        0% {{ transform: translate(0, 0) rotate(0deg); }}
        100% {{ transform: translate(-50px, -50px) rotate(360deg); }}
    }}
    #loading-title {{ 
        font-size: 4em; 
        margin-bottom: 10px; 
        font-weight: 800; 
        color: #fff; 
        text-shadow: 0 4px 20px rgba(0,0,0,0.3), 0 2px 10px rgba(255,255,255,0.2);
        animation: titleFloat 3s ease-in-out infinite, slideDown 0.8s ease-out;
        letter-spacing: 2px;
        position: relative;
        z-index: 1;
    }}
    @keyframes titleFloat {{
        0%, 100% {{ transform: translateY(0) scale(1); }}
        50% {{ transform: translateY(-10px) scale(1.02); }}
    }}
    @keyframes slideDown {{
        from {{ opacity: 0; transform: translateY(-30px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    #loading-subtitle {{ 
        font-size: 1.3em; 
        margin-bottom: 50px; 
        color: rgba(255,255,255,0.95); 
        font-weight: 400; 
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
        animation: fadeInUp 1s ease-out 0.3s both;
        letter-spacing: 1px;
        position: relative;
        z-index: 1;
    }}
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    #start-button {{ 
        padding: 20px 50px; 
        font-size: 1.5em; 
        font-weight: 700; 
        border: none; 
        border-radius: 50px; 
        background: linear-gradient(135deg, #FFC107 0%, #FFD54F 100%);
        color: #2c3e50; 
        cursor: pointer; 
        box-shadow: 0 8px 30px rgba(255,193,7,0.4), 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        z-index: 1;
        animation: buttonPulse 2s ease-in-out infinite, fadeInUp 1s ease-out 0.6s both;
        letter-spacing: 1px;
    }}
    @keyframes buttonPulse {{
        0%, 100% {{ box-shadow: 0 8px 30px rgba(255,193,7,0.4), 0 4px 15px rgba(0,0,0,0.2); }}
        50% {{ box-shadow: 0 12px 40px rgba(255,193,7,0.6), 0 6px 20px rgba(0,0,0,0.3); }}
    }}
    #start-button::before {{
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255,255,255,0.5);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }}
    #start-button:hover::before {{
        width: 400px;
        height: 400px;
    }}
    #start-button:hover {{
        background: linear-gradient(135deg, #FFD54F 0%, #FFC107 100%);
        transform: translateY(-5px) scale(1.05);
        box-shadow: 0 15px 45px rgba(255,193,7,0.5), 0 8px 25px rgba(0,0,0,0.3);
    }}
    #start-button:active {{
        transform: translateY(-2px) scale(1.02);
    }}
    #start-button > * {{
        position: relative;
        z-index: 1;
    }}
    /* --- その他のUIスタイル (変更なし) --- */

    body {{ margin: 0; overflow: hidden; }}
    #map_{map_name} {{ position: absolute; top: 0; bottom: 0; right: 0; left: 0; z-index: 1; }}

    #sidebar {{ 
        position: fixed; top: 0; right: 0; width: 320px; height: 100%; 
        background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%); 
        z-index: 100000; padding: 0; transform: translateX(100%); 
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
        box-shadow: -4px 0 20px rgba(0,0,0,0.15); 
        font-family: 'Segoe UI', Arial, sans-serif; 
        display: flex; flex-direction: column; overflow-y: auto;
    }}
    #sidebar.open {{ transform: translateX(0); }}
    #sidebar h2 {{ 
        color: #fff; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px; margin: 0; border-bottom: none;
        display: flex; align-items: center; justify-content: space-between;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }}
    #sidebar h2 .close-btn {{ 
        background: rgba(255,255,255,0.2); border: none; 
        font-size: 1.5em; cursor: pointer; color: #fff; 
        padding: 5px 10px; line-height: 1; border-radius: 50%;
        transition: background-color 0.2s;
    }}
    #sidebar h2 .close-btn:hover {{ background: rgba(255,255,255,0.3); }}
    .sidebar-item {{ 
        display: flex; align-items: center; padding: 18px 20px; 
        text-decoration: none; color: #333; 
        border-bottom: 1px solid #eee; 
        transition: all 0.2s; cursor: pointer;
        background: #fff;
        min-height: 55px;
    }}
    .sidebar-item:hover {{ 
        background: linear-gradient(90deg, #f0f4ff 0%, #fff 100%);
        padding-left: 25px;
    }}
    #sidebar hr {{ border: none; border-top: 2px solid #e0e0e0; margin: 15px 20px; }}
    #sidebar h3 {{ 
        color: #555; margin: 20px 20px 10px 20px; font-size: 1.1em; 
        font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
    }}
    .filter-item {{ 
        display: flex; align-items: center; padding: 15px 20px; 
        cursor: pointer; user-select: none; 
        background: #fff; margin: 0 10px 8px 10px;
        border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: all 0.2s;
        min-height: 50px;
    }}
    .filter-item:hover {{ 
        background: linear-gradient(90deg, #f0f4ff 0%, #fff 100%);
        transform: translateX(5px);
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    }}
    .filter-item label {{ 
        display: flex; align-items: center; width: 100%; 
        cursor: pointer; gap: 10px;
    }}
    .filter-item input[type="checkbox"] {{
        width: 24px; height: 24px; cursor: pointer;
        accent-color: #667eea;
        min-width: 24px; min-height: 24px;
    }}
    .filter-item.filter-all {{
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        margin: 10px;
    }}
    .filter-item.filter-all:hover {{
        background: linear-gradient(135deg, #45a049 0%, #4CAF50 100%);
        transform: translateX(0) scale(1.02);
    }}
    .filter-item.filter-all label {{
        color: white;
    }}
    .filter-item.filter-all input[type="checkbox"] {{
        accent-color: white;
    }}

    #hamburger {{ 
        position: fixed; top: 20px; right: 20px; z-index: 100001; 
        cursor: pointer; width: 50px; height: 50px; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 50%; 
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); 
        display: flex; flex-direction: column; 
        justify-content: center; align-items: center; 
        padding: 12px; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    #hamburger:hover {{
        transform: scale(1.1) rotate(90deg);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }}
    #sidebar.open ~ #hamburger {{ 
        display: none; 
    }}
    .bar {{ 
        width: 24px; height: 3px; background-color: #fff; 
        border-radius: 2px; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        margin: 2px 0;
    }}
    #hamburger:hover .bar {{
        background-color: #f0f0f0;
    }}

    #locate-button {{
        position: fixed; 
        bottom: 20px; 
        left: 20px;
        z-index: 100005; 
        background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
        color: white; 
        border: none; 
        width: 64px; 
        height: 64px; 
        border-radius: 50%; 
        font-size: 1.6em; 
        display: flex; 
        justify-content: center; 
        align-items: center; 
        box-shadow: 0 8px 20px rgba(255,152,0,0.4), 0 4px 8px rgba(0,0,0,0.1); 
        cursor: pointer; 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        min-width: 64px; 
        min-height: 64px;
        overflow: hidden;
    }}
    #locate-button::before {{
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255,255,255,0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }}
    #locate-button:hover::before {{
        width: 300px;
        height: 300px;
    }}
    #locate-button:hover {{
        background: linear-gradient(135deg, #F57C00 0%, #FF9800 100%);
        transform: scale(1.08) translateY(-2px);
        box-shadow: 0 12px 28px rgba(255,152,0,0.5), 0 6px 12px rgba(0,0,0,0.15);
    }}
    #locate-button:active {{
        transform: scale(1.02) translateY(0);
    }}

    /* 条件検索ボタンのスタイル */
    #filter-search-button {{
        position: fixed; 
        bottom: 20px; 
        right: 20px; 
        width: 64px; 
        height: 64px; 
        border-radius: 50%; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        font-size: 1.6em; 
        display: flex; 
        justify-content: center; 
        align-items: center; 
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4), 0 4px 8px rgba(0,0,0,0.1); 
        cursor: pointer; 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        min-width: 64px; 
        min-height: 64px;
        overflow: hidden;
        z-index: 100004;
    }}
    #filter-search-button::before {{
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255,255,255,0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }}
    #filter-search-button:hover::before {{
        width: 300px;
        height: 300px;
    }}
    #filter-search-button:hover {{
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        transform: scale(1.08) translateY(-2px);
        box-shadow: 0 12px 28px rgba(102, 126, 234, 0.5), 0 6px 12px rgba(0,0,0,0.15);
    }}
    #filter-search-button:active {{
        transform: scale(1.02) translateY(0);
    }}

    /* 企業取引ボタンのスタイル */
    #business-button {{
        position: fixed; 
        bottom: 100px; 
        right: 20px; 
        width: 64px; 
        height: 64px; 
        border-radius: 50%; 
        background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);
        color: white;
        border: none;
        font-size: 1.6em; 
        display: flex; 
        justify-content: center; 
        align-items: center; 
        box-shadow: 0 8px 20px rgba(76, 175, 80, 0.4), 0 4px 8px rgba(0,0,0,0.1); 
        cursor: pointer; 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        min-width: 64px; 
        min-height: 64px;
        overflow: hidden;
        z-index: 100004;
    }}
    #business-button::before {{
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255,255,255,0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }}
    #business-button:hover::before {{
        width: 300px;
        height: 300px;
    }}
    #business-button:hover {{
        background: linear-gradient(135deg, #388E3C 0%, #4CAF50 100%);
        transform: scale(1.08) translateY(-2px);
        box-shadow: 0 12px 28px rgba(76, 175, 80, 0.5), 0 6px 12px rgba(0,0,0,0.15);
    }}
    #business-button:active {{
        transform: scale(1.02) translateY(0);
    }}
    /* リスト項目 (アプリ風デザイン・クリックしやすく改善) */
    #super-list li {{ 
        padding: 20px; margin-bottom: 14px; 
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        border-radius: 16px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04); 
        cursor: pointer; 
        display: flex; align-items: center; justify-content: space-between; 
        border-left: 5px solid;
        border-image: linear-gradient(135deg, #667eea 0%, #764ba2 100%) 1;
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        min-height: 72px;
        backdrop-filter: blur(10px);
    }}
    #super-list li::before {{
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        height: 100%;
        width: 0;
        background: linear-gradient(90deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.1) 100%);
        transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        z-index: 0;
    }}
    #super-list li::after {{
        content: '';
        position: absolute;
        right: 20px;
        top: 50%;
        transform: translateY(-50%) translateX(0);
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        opacity: 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    #super-list li > * {{
        position: relative;
        z-index: 1;
    }}
    #super-list li:hover {{
        background: linear-gradient(135deg, #f0f4ff 0%, #ffffff 100%);
        transform: translateX(8px) translateY(-3px);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2), 0 4px 8px rgba(0,0,0,0.1);
        border-left-width: 6px;
    }}
    #super-list li:hover::before {{
        width: 100%;
    }}
    #super-list li:hover::after {{
        opacity: 1;
        transform: translateY(-50%) translateX(-4px);
        width: 12px;
        height: 12px;
    }}
    #super-list li:active {{
        transform: translateX(6px) translateY(-1px);
    }}

    #super-list li .info-block {{ flex-grow: 1; margin-left: 14px; }}
    #super-list li .store-name {{ font-weight: 600; font-size: 1.15em; color: #2c3e50; display: block; letter-spacing: 0.3px; }}
    #super-list li .brand-name {{ font-size: 0.9em; color: #7f8c8d; display: block; margin-top: 5px; font-weight: 500; }}

    #super-list li img {{ 
        height: 42px; width: 42px; object-fit: contain; flex-shrink: 0; 
        border-radius: 12px; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    #super-list li:hover img {{
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}

    #super-list li .distance-info {{ 
        font-size: 1.2em; font-weight: 700; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        white-space: nowrap; 
        letter-spacing: 0.5px;
    }}

    /* 地図上の情報オーバーレイ */
    #map-info {{
        position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 249, 250, 0.95) 100%);
        padding: 12px 20px; border-radius: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2); z-index: 100000; 
        font-size: 0.9em; text-align: center; color: #333; 
        font-weight: 600; max-width: 90%;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.5);
    }}

    /* 比較パネルのスタイル */
    #comparison-panel {{
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(0, 0, 0, 0.8); z-index: 100006;
        display: none; justify-content: center; align-items: center;
    }}
    #comparison-content {{
        background-color: #fff; border-radius: 8px; width: 90%; max-width: 500px;
        max-height: 85vh; padding: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.5);
        display: flex; flex-direction: column;
    }}
    #comparison-data {{
        overflow-y: auto; overflow-x: hidden;
        flex: 1; padding-right: 5px;
        max-height: calc(85vh - 80px);
    }}
    #comparison-data::-webkit-scrollbar {{
        width: 8px;
    }}
    #comparison-data::-webkit-scrollbar-track {{
        background: #f1f1f1; border-radius: 10px;
    }}
    #comparison-data::-webkit-scrollbar-thumb {{
        background: #888; border-radius: 10px;
    }}
    #comparison-data::-webkit-scrollbar-thumb:hover {{
        background: #555;
    }}
    .comparison-item {{
        padding: 8px 0; border-bottom: 1px dotted #ddd;
    }}
    .comparison-item:last-child {{ border-bottom: none; }}

    /* フィルタリング結果パネルのスタイル */
    #filter-results-panel {{
        position: fixed; 
        bottom: 100px; 
        right: 20px; 
        width: 400px; 
        max-height: calc(100vh - 120px); 
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        border-radius: 24px; 
        box-shadow: 0 20px 60px rgba(0,0,0,0.3), 0 8px 16px rgba(0,0,0,0.2); 
        z-index: 100003; 
        display: none;
        flex-direction: column;
        font-family: 'Segoe UI', Arial, sans-serif;
        border: 1px solid rgba(255,255,255,0.5);
        backdrop-filter: blur(20px);
        animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    @keyframes slideUp {{
        from {{ opacity: 0; transform: translateY(60px) scale(0.95); }}
        to {{ opacity: 1; transform: translateY(0) scale(1); }}
    }}
    #filter-results-content {{
        display: flex; 
        flex-direction: column; 
        overflow: hidden;
        max-height: 100%;
    }}
    #filter-results-content h2 {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 20px 24px; margin: 0;
        border-radius: 24px 24px 0 0;
        display: flex; align-items: center; justify-content: space-between;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        font-size: 1.2em;
        font-weight: 600;
        letter-spacing: 0.5px;
    }}
    #filter-results-content h2 .close-btn-results {{
        background: rgba(255,255,255,0.2); border: none; 
        font-size: 1.5em; cursor: pointer; color: #fff; 
        padding: 5px 10px; line-height: 1; border-radius: 50%;
        transition: background-color 0.2s;
    }}
    #filter-results-content h2 .close-btn-results:hover {{
        background: rgba(255,255,255,0.3);
    }}
    #filter-results-list {{
        padding: 20px; overflow-y: auto; flex: 1;
        background: linear-gradient(to bottom, transparent 0%, rgba(248,249,255,0.5) 100%);
        max-height: calc(100vh - 200px);
    }}
    #filter-results-list::-webkit-scrollbar {{
        width: 8px;
    }}
    #filter-results-list::-webkit-scrollbar-track {{
        background: rgba(0,0,0,0.05);
        border-radius: 4px;
    }}
    #filter-results-list::-webkit-scrollbar-thumb {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 4px;
    }}
    #filter-results-list::-webkit-scrollbar-thumb:hover {{
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }}
    #filter-results-list .result-item {{
        padding: 18px; margin-bottom: 12px; 
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        border-radius: 16px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04); 
        cursor: pointer; 
        display: flex; 
        align-items: center; 
        justify-content: space-between; 
        border-left: 5px solid;
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }}
    #filter-results-list .result-item:hover {{
        background: linear-gradient(135deg, #f0f4ff 0%, #ffffff 100%);
        transform: translateX(8px) translateY(-3px);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2), 0 4px 8px rgba(0,0,0,0.1);
        border-left-width: 6px;
    }}
    #filter-results-list .result-item img {{
        height: 42px; width: 42px; object-fit: contain; flex-shrink: 0; 
        border-radius: 12px; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    #filter-results-list .result-item:hover img {{
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    #filter-results-list .result-item .result-info {{
        flex-grow: 1; margin-left: 14px;
    }}
    #filter-results-list .result-item .result-store-name {{
        font-weight: 600; font-size: 1.15em; color: #2c3e50; display: block; letter-spacing: 0.3px;
    }}
    #filter-results-list .result-item .result-brand-name {{
        font-size: 0.9em; color: #7f8c8d; display: block; margin-top: 5px; font-weight: 500;
    }}
    
    /* モバイル対応 - スマートフォン用スタイル */
    @media screen and (max-width: 768px) {{
        /* サイドバーの幅を全画面に */
        #sidebar {{
            width: 100% !important;
            max-width: 100% !important;
        }}
        
        /* ハンバーガーメニューのサイズ調整 */
        #hamburger {{
            width: 44px !important;
            height: 44px !important;
            top: 15px !important;
            right: 15px !important;
            padding: 8px !important;
        }}
        
        /* ボタンのサイズを大きく（タッチしやすく） */
        #locate-button, #filter-search-button, #business-button {{
            width: 56px !important;
            height: 56px !important;
            min-width: 56px !important;
            min-height: 56px !important;
            font-size: 1.4em !important;
            bottom: 15px !important;
        }}
        
        #locate-button {{
            left: 15px !important;
        }}
        
        #filter-search-button {{
            right: 15px !important;
        }}
        
        #business-button {{
            right: 15px !important;
            bottom: 80px !important;
        }}
        
        /* 比較パネルのサイズ調整 */
        #comparison-content {{
            width: 95% !important;
            max-width: 95% !important;
            max-height: 90vh !important;
            padding: 20px !important;
        }}
        
        /* カテゴリーボタンのグリッド調整 */
        #comparison-data button {{
            padding: 18px 15px !important;
            font-size: 1em !important;
        }}
        
        /* フィルタリング結果パネルの調整 */
        #filter-results-panel {{
            width: 100% !important;
            max-width: 100% !important;
        }}
        
        #filter-results-content {{
            width: 100% !important;
            max-width: 100% !important;
            max-height: 90vh !important;
        }}
        
        /* 地図情報バーの調整 */
        #map-info {{
            top: 5px !important;
            left: 5px !important;
            right: 5px !important;
            transform: none !important;
            max-width: calc(100% - 10px) !important;
            padding: 10px 15px !important;
            font-size: 0.85em !important;
        }}
        
        /* リストアイテムの調整 */
        #super-list li {{
            padding: 15px !important;
            min-height: 60px !important;
        }}
        
        #super-list li .store-name {{
            font-size: 1em !important;
        }}
        
        #super-list li .brand-name {{
            font-size: 0.85em !important;
        }}
        
        #super-list li .distance-info {{
            font-size: 1em !important;
        }}
        
        /* サイドバーアイテムの調整 */
        .sidebar-item {{
            padding: 15px 12px !important;
            font-size: 1em !important;
            min-height: 48px !important;
        }}
        
        /* ローディング画面の調整 */
        #loading-title {{
            font-size: 1.8em !important;
            padding: 0 20px !important;
        }}
        
        #loading-subtitle {{
            font-size: 0.9em !important;
            padding: 0 20px !important;
        }}
        
        #start-button {{
            padding: 18px 40px !important;
            font-size: 1.2em !important;
        }}
        
        /* ポップアップの調整 */
        .leaflet-popup-content {{
            max-width: 280px !important;
            font-size: 0.9em !important;
        }}
        
        .leaflet-popup-content button {{
            padding: 10px !important;
            font-size: 0.9em !important;
        }}
        
        /* カテゴリー選択ボタンのグリッドを1列に */
        #comparison-data > div:last-child {{
            grid-template-columns: 1fr !important;
        }}
    }}
    
    /* タッチデバイス用の調整 */
    @media (hover: none) and (pointer: coarse) {{
        /* ホバー効果をタッチに適応 */
        #super-list li:active {{
            background: linear-gradient(135deg, #f0f4ff 0%, #ffffff 100%) !important;
            transform: translateX(4px) translateY(-2px) !important;
        }}
        
        .sidebar-item:active {{
            background-color: #f0f0f0 !important;
        }}
        
        button:active {{
            transform: scale(0.95) !important;
        }}
    }}
</style>

<div id="loading-mask">
    <div id="loading-title"><i class="fas fa-map-marked-alt"></i> SMAP - Supermarket Map App</div>
    <div id="loading-subtitle">福山市内の全店舗の特売情報と、最寄り店舗をすぐに検索！ (全{df.shape[0]}店舗)</div>
    <button id="start-button" onclick="startApp()"><i class="fas fa-play-circle"></i> マップを起動する</button>
</div>

<div id="map-info">
    <i class="fas fa-search-location" style="color:#007bff;"></i> スーパーマーケット情報
    <span id="map-info-text" style="display: block; font-size: 0.8em; font-weight: normal; color: #555;">(基準点: 穴吹ビジネス専門学校)</span>
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
    <h3><i class="fas fa-route"></i> ブランド別距離情報</h3>
    <p style="padding: 0 15px; margin-bottom: 10px; font-size: 0.9em; color: #666;">
        ブランドをタップすると距離一覧が表示されます
    </p>
"""
# 各ブランドのタップ可能なアイテムを動的に追加
for brand, color in PIN_COLORS.items():
    # ブランド名を安全にエスケープ
    brand_escaped = brand.replace('"', '&quot;').replace("'", "\\'")
    app_ui_elements += f"""
    <div class="sidebar-item" onclick='showBrandDistance("{brand_escaped}")' style="cursor: pointer; border-left: 4px solid {color};">
        <i class="fas fa-store" style="color: {color};"></i> {brand}
        <i class="fas fa-chevron-right" style="float: right; color: #999; margin-top: 2px;"></i>
    </div>
    """
app_ui_elements += rf"""
    <h3><i class="fas fa-info-circle"></i> ヘルプ・その他</h3>
    <a href="faq.html" class="sidebar-item" style="text-decoration: none; display: flex; align-items: center;" onclick="toggleSidebar();">
        <i class="fas fa-question-circle"></i> よくある質問 (FAQ)
    </a>
    <a href="contact.html" class="sidebar-item" style="text-decoration: none; display: flex; align-items: center;" onclick="toggleSidebar();">
        <i class="fas fa-envelope"></i> お問い合わせ
    </a>
</div>

<div id="hamburger" onclick="toggleSidebar()">
    <div class="bar"></div>
    <div class="bar"></div>
    <div class="bar"></div>
</div>

<button id="locate-button" onclick="locateUser()">
    <i class="fas fa-street-view"></i>
</button>

<button id="business-button" onclick="showBusinessInfo()" title="企業取引">
    <i class="fas fa-handshake"></i>
</button>

<div id="filter-results-panel" style="display: none;">
    <div id="filter-results-content">
        <h2>
            <i class="fas fa-filter"></i> フィルタリング結果
            <button class="close-btn-results" onclick="document.getElementById('filter-results-panel').style.display='none';"><i class="fas fa-times"></i></button>
        </h2>
        <div id="filter-results-list">
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
    const generated_pin_base64_js = {json.dumps(generated_pin_base64)};

    // --- 基準点とデモ現在地の定義 ---
    const INITIAL_REFERENCE_LAT = 34.49178298;
    const INITIAL_REFERENCE_LON = 133.3690471;
    const INITIAL_REFERENCE_NAME = "穴吹ビジネス専門学校";

    const DEMO_LOCATION_LAT = 34.485; 
    const DEMO_LOCATION_LON = 133.365;
    const DEMO_REFERENCE_NAME = "デモ現在地 (ボタン)";

    // 企業取引認証キー（開発者と企業間で共有）
    const BUSINESS_ACCESS_KEY = {json.dumps(BUSINESS_ACCESS_KEY)};
    const BUSINESS_AUTH_STORAGE_KEY = 'business_auth_verified';

    // 現在使用している基準点
    let currentReferenceLat = INITIAL_REFERENCE_LAT;
    let currentReferenceLon = INITIAL_REFERENCE_LON;
    let currentReferenceName = INITIAL_REFERENCE_NAME;
    let currentLocationMarker = null; // 現在地のマーカーを保持するための変数

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
        const R = 6371; 
        const dLat = (lat2 - lat1) * (Math.PI / 180);
        const dLon = (lon2 - lon1) * (Math.PI / 180);
        const a =
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return Math.round(R * c * 1000);
    }}

    $(document).ready(function() {{
        // 初期状態で全てのブランドが表示されるようにする
        // DOM構築完了
        // ★修正点：初期状態でマップクリックイベントを登録★
        mapElement.on('click', onMapClick); 
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


    // ★★★ 修正: locateUser() 関数 (デモ現在地の設定) ★★★
    function locateUser() {{
        alert("現在地を福山市中心付近に設定し、最寄り店舗を計算します。\n(このボタンはデモ機能です。地図上の任意の場所をクリックして基準点を設定することもできます。)");

        // 基準点をデモ現在地に切り替え
        currentReferenceLat = DEMO_LOCATION_LAT;
        currentReferenceLon = DEMO_LOCATION_LON;
        currentReferenceName = DEMO_REFERENCE_NAME;

        // マップをデモ現在地に移動
        mapElement.setView([currentReferenceLat, currentReferenceLon], 14);

        updateReferenceMarker();
    }}
    // ★★★ 修正: locateUser() 関数 終わり ★★★
    
    // ★★★ 新規追加: onMapClick 関数 (地図クリックで現在地設定) ★★★
    function onMapClick(e) {{
        currentReferenceLat = e.latlng.lat;
        currentReferenceLon = e.latlng.lng;
        currentReferenceName = `クリック地点 (${{currentReferenceLat.toFixed(4)}}, ${{currentReferenceLon.toFixed(4)}})`;

        updateReferenceMarker();
    }}

    // ★★★ 新規追加: 基準点マーカーの更新処理を共通化 ★★★
    function updateReferenceMarker() {{
        // 既存の現在地マーカーを削除
        if (currentLocationMarker) {{
            mapElement.removeLayer(currentLocationMarker);
            currentLocationMarker = null;
        }}

        // 新しい基準点マーカーを設置
        currentLocationMarker = L.marker([currentReferenceLat, currentReferenceLon], {{
            icon: L.divIcon({{
                className: 'current-location-marker',
                html: '<div style="color: #FF9800; font-size: 20px; text-align: center;"><i class="fas fa-map-marker-alt fa-2x"></i></div>', // 地図クリック用にアイコン変更
                iconSize: [40, 40],
                iconAnchor: [15, 30] // ピンの先端が座標に来るように調整
            }}),
            zIndexOffset: 2000
        }}).addTo(mapElement).bindPopup(`${{currentReferenceName}}`).openPopup();
        
        // 地図上の情報オーバーレイを更新
        $('#map-info-text').html(`(基準点: ${{currentReferenceName}} Lat: ${{currentReferenceLat.toFixed(4)}}, Lon: ${{currentReferenceLon.toFixed(4)}})`);
    }}

    function openMarkerPopup(lat, lon, layerId) {{
        const currentZoom = mapElement.getZoom();
        const targetZoom = Math.max(currentZoom, 14);

        mapElement.setView([lat, lon], targetZoom);

        mapElement.eachLayer(layer => {{
            if (layer._leaflet_id === layerId) {{
                if (layer.openPopup) {{
                    layer.openPopup();
                    return;
                }}
            }}
        }});
    }}



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

        mapElement.closePopup();
    }}

    // ブランド別の距離詳細を表示する関数
    function showBrandDistance(brandName) {{
        console.log('showBrandDistance called with:', brandName);
        console.log('allMarkersData:', allMarkersData);
        
        if (!brandName) {{
            alert('ブランド名が指定されていません');
            return;
        }}
        
        const filteredStores = allMarkersData.filter(d => d.brand === brandName);
        console.log('Filtered stores for brand', brandName, ':', filteredStores.length);
        
        if (filteredStores.length === 0) {{
            alert(brandName + 'の店舗が見つかりません');
            return;
        }}
        
        const storesWithDistance = filteredStores.map(store => ({{
            ...store,
            distance: store.distance || 0,
            distanceKm: ((store.distance || 0) / 1000).toFixed(2),
            distanceM: Math.round(store.distance || 0)
        }})).sort((a, b) => (a.distance || 0) - (b.distance || 0));

        const panel = document.getElementById('comparison-panel');
        if (!panel) {{
            alert('距離表示パネルが見つかりません');
            console.error('comparison-panel element not found');
            return;
        }}
        
        const titleEl = document.getElementById('comparison-store-name');
        if (titleEl) {{
            titleEl.textContent = brandName + 'の各店舗の距離';
        }}
        
        let detailHtml = '<div style="margin-bottom: 15px; padding: 10px; background: #f0f4ff; border-radius: 8px;">' +
            '<p style="margin: 0; font-size: 0.9em; color: #667eea;"><i class="fas fa-map-marker-alt"></i> 基準点: 穴吹ビジネス専門学校から</p>' +
            '<p style="margin: 5px 0 0 0; font-size: 0.85em; color: #999;">全' + storesWithDistance.length + '店舗</p>' +
            '</div>';
        
        storesWithDistance.forEach(store => {{
            const brandColor = PIN_COLORS_JS[store.brand] || '#333';
            const markerIndex = parseInt(store.id.replace('marker-', '')) || -1;
            const logoBase64Url = markerIndex >= 0 ? (generated_pin_base64_js[markerIndex] || '') : '';
            
            detailHtml += '<div class="comparison-item" style="padding: 12px; margin-bottom: 8px; border-left: 4px solid ' + brandColor + '; background: #f9f9f9; border-radius: 4px; cursor: pointer;" onclick="openMarkerPopup(' + store.lat + ', ' + store.lon + ', ' + store.layer_id + '); document.getElementById(\'comparison-panel\').style.display=\'none\';">' +
                '<div style="display: flex; align-items: center; gap: 10px;">' +
                (logoBase64Url ? '<img src="' + logoBase64Url + '" style="height: 30px; width: 30px; object-fit: contain; cursor: pointer;" onerror="this.style.display=\'none\'" onclick="openMarkerPopup(' + store.lat + ', ' + store.lon + ', ' + store.layer_id + '); document.getElementById(\'comparison-panel\').style.display=\'none\'; event.stopPropagation();">' : '') +
                '<div style="flex: 1;">' +
                '<p style="margin: 0; font-weight: 600; color: #333; font-size: 1em;"><i class="fas fa-store" style="color: ' + brandColor + ';"></i> ' + store.name + '</p>' +
                '<p style="margin: 5px 0 0 0; font-size: 1.1em; color: #667eea; font-weight: 700;">' + store.distanceM + ' m (' + store.distanceKm + ' km)</p>' +
                '</div></div></div>';
        }});

        const dataEl = document.getElementById('comparison-data');
        if (dataEl) {{
            dataEl.innerHTML = detailHtml;
        }} else {{
            console.error('comparison-data element not found');
            alert('データ表示エリアが見つかりません');
            return;
        }}
        
        panel.style.display = 'flex';
        if (typeof $ !== 'undefined' && $.fn.fadeIn) {{
            $(panel).fadeIn(200);
        }}
        
        if (mapElement && mapElement.closePopup) {{
            mapElement.closePopup();
        }}
        
        // サイドバーは開いたままにする（距離パネルと同時表示）
        
        console.log('Distance panel displayed successfully');
    }}

    // カテゴリー選択画面を表示する関数
    function showCategorySelector(storeName, markerIndex) {{
        const store = allMarkersData.find(d => d.name === storeName);
        if (!store) {{
            alert('店舗情報が見つかりません');
            return;
        }}
        
        const panel = document.getElementById('comparison-panel');
        if (!panel) {{
            alert('パネルが見つかりません');
            return;
        }}
        
        const titleEl = document.getElementById('comparison-store-name');
        if (titleEl) {{
            titleEl.textContent = storeName + ' の詳細情報';
        }}
        
        const categoryHtml = '<div style="margin-bottom: 20px; padding: 15px; background: linear-gradient(135deg, #f0f4ff 0%, #fff 100%); border-radius: 10px; border-left: 4px solid #667eea;">' +
            '<p style="margin: 0; font-size: 0.9em; color: #667eea;"><i class="fas fa-info-circle"></i> 見たいカテゴリーを選択してください</p>' +
            '</div>' +
            '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">' +
            '<button onclick="showCategoryInfo(\'' + storeName + '\', \'sengyo\')" style="padding: 20px; background: linear-gradient(135deg, #00BCD4 0%, #0097A7 100%); color: white; border: none; border-radius: 12px; cursor: pointer; font-size: 1.1em; font-weight: bold; transition: all 0.3s; box-shadow: 0 4px 15px rgba(0,188,212,0.3);">' +
            '<i class="fas fa-fish" style="font-size: 1.5em; display: block; margin-bottom: 8px;"></i>鮮魚' +
            '</button>' +
            '<button onclick="showCategoryInfo(\'' + storeName + '\', \'niku\')" style="padding: 20px; background: linear-gradient(135deg, #E91E63 0%, #C2185B 100%); color: white; border: none; border-radius: 12px; cursor: pointer; font-size: 1.1em; font-weight: bold; transition: all 0.3s; box-shadow: 0 4px 15px rgba(233,30,99,0.3);">' +
            '<i class="fas fa-drumstick-bite" style="font-size: 1.5em; display: block; margin-bottom: 8px;"></i>精肉' +
            '</button>' +
            '<button onclick="showCategoryInfo(\'' + storeName + '\', \'souzai\')" style="padding: 20px; background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); color: white; border: none; border-radius: 12px; cursor: pointer; font-size: 1.1em; font-weight: bold; transition: all 0.3s; box-shadow: 0 4px 15px rgba(255,152,0,0.3);">' +
            '<i class="fas fa-utensils" style="font-size: 1.5em; display: block; margin-bottom: 8px;"></i>惣菜' +
            '</button>' +
            '<button onclick="showCategoryInfo(\'' + storeName + '\', \'seika\')" style="padding: 20px; background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%); color: white; border: none; border-radius: 12px; cursor: pointer; font-size: 1.1em; font-weight: bold; transition: all 0.3s; box-shadow: 0 4px 15px rgba(76,175,80,0.3);">' +
            '<i class="fas fa-carrot" style="font-size: 1.5em; display: block; margin-bottom: 8px;"></i>青果' +
            '</button>' +
            '</div>';
        
        const dataEl = document.getElementById('comparison-data');
        if (dataEl) {{
            dataEl.innerHTML = categoryHtml;
        }}
        
        panel.style.display = 'flex';
        if (typeof $ !== 'undefined' && $.fn.fadeIn) {{
            $(panel).fadeIn(200);
        }}
        
        if (mapElement && mapElement.closePopup) {{
            mapElement.closePopup();
        }}
    }}
    
    // カテゴリーごとの情報を表示する関数
    function showCategoryInfo(storeName, category) {{
        const store = allMarkersData.find(d => d.name === storeName);
        if (!store) {{
            alert('店舗情報が見つかりません');
            return;
        }}
        
        const categoryNames = {{
            'sengyo': {{ name: '鮮魚', icon: 'fas fa-fish', color: '#00BCD4' }},
            'niku': {{ name: '精肉', icon: 'fas fa-drumstick-bite', color: '#E91E63' }},
            'souzai': {{ name: '惣菜', icon: 'fas fa-utensils', color: '#FF9800' }},
            'seika': {{ name: '青果', icon: 'fas fa-carrot', color: '#4CAF50' }}
        }};
        
        const catInfo = categoryNames[category] || {{ name: '情報', icon: 'fas fa-info', color: '#666' }};
        const info = store[category] || '情報が登録されていません';
        
        const panel = document.getElementById('comparison-panel');
        if (!panel) return;
        
        const titleEl = document.getElementById('comparison-store-name');
        if (titleEl) {{
            titleEl.innerHTML = '<i class="' + catInfo.icon + '" style="color: ' + catInfo.color + ';"></i> ' + storeName + ' - ' + catInfo.name;
        }}
        
        const infoHtml = '<div style="margin-bottom: 15px; padding: 15px; background: linear-gradient(135deg, #f0f4ff 0%, #fff 100%); border-radius: 10px; border-left: 4px solid ' + catInfo.color + ';">' +
            '<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">' +
            '<div style="width: 50px; height: 50px; background: ' + catInfo.color + '; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 1.5em;">' +
            '<i class="' + catInfo.icon + '"></i>' +
            '</div>' +
            '<div>' +
            '<h3 style="margin: 0; color: #333; font-size: 1.3em;">' + catInfo.name + '情報</h3>' +
            '<p style="margin: 5px 0 0 0; color: #666; font-size: 0.9em;">' + storeName + '</p>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '<div style="padding: 20px; background: #fff; border-radius: 10px; border: 2px solid #e0e0e0; line-height: 1.8; color: #555; font-size: 1em; white-space: pre-wrap;">' +
            info +
            '</div>' +
            '<button onclick="showCategorySelector(\'' + storeName + '\', 0)" style="margin-top: 15px; padding: 10px 20px; background: #f0f0f0; border: none; border-radius: 8px; cursor: pointer; font-weight: 500; color: #333; width: 100%; transition: all 0.3s;">' +
            '<i class="fas fa-arrow-left"></i> カテゴリー選択に戻る' +
            '</button>';
        
        const dataEl = document.getElementById('comparison-data');
        if (dataEl) {{
            dataEl.innerHTML = infoHtml;
        }}
    }}

    // 企業取引情報を表示する関数（認証キー必須）
    function showBusinessInfo() {{
        // LocalStorageに認証済みフラグがあるか確認
        const isVerified = localStorage.getItem(BUSINESS_AUTH_STORAGE_KEY) === 'true';
        
        if (!isVerified) {{
            // 認証キーの入力を要求
            const inputKey = prompt('企業取引情報にアクセスするには認証キーが必要です。\\n\\n認証キーを入力してください：');
            
            if (!inputKey) {{
                // キャンセルされた場合
                return;
            }}
            
            // 認証キーの検証
            if (inputKey.trim() !== BUSINESS_ACCESS_KEY) {{
                alert('認証キーが正しくありません。\\n\\n企業取引に関するお問い合わせは、開発者までご連絡ください。');
                return;
            }}
            
            // 認証成功：LocalStorageに保存（30日間有効）
            localStorage.setItem(BUSINESS_AUTH_STORAGE_KEY, 'true');
            const expiryDate = new Date();
            expiryDate.setDate(expiryDate.getDate() + 30);
            localStorage.setItem('business_auth_expiry', expiryDate.toISOString());
        }} else {{
            // 有効期限を確認
            const expiryDate = localStorage.getItem('business_auth_expiry');
            if (expiryDate && new Date(expiryDate) < new Date()) {{
                // 有効期限切れ
                localStorage.removeItem(BUSINESS_AUTH_STORAGE_KEY);
                localStorage.removeItem('business_auth_expiry');
                const inputKey = prompt('認証キーの有効期限が切れています。\\n\\n認証キーを再入力してください：');
                if (!inputKey || inputKey.trim() !== BUSINESS_ACCESS_KEY) {{
                    alert('認証キーが正しくありません。');
                    return;
                }}
                localStorage.setItem(BUSINESS_AUTH_STORAGE_KEY, 'true');
                const newExpiryDate = new Date();
                newExpiryDate.setDate(newExpiryDate.getDate() + 30);
                localStorage.setItem('business_auth_expiry', newExpiryDate.toISOString());
            }}
        }}
        
        // 認証済みなので企業向けフォームページにリダイレクト
        window.location.href = 'business_form.html';
    }}


</script>
"""

# 5-2. マップをHTMLファイルとして保存し、UIを挿入
file_path = "supermarket_app_map_clickable_list.html"
m_temp.save(file_path)

with open(file_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# <head>タグ内にviewportメタタグを追加（モバイル対応）
if '<meta name="viewport"' not in html_content:
    head_insertion_point = html_content.find('</head>')
    if head_insertion_point != -1:
        viewport_meta = '    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">\n'
        html_content = html_content[:head_insertion_point] + viewport_meta + html_content[head_insertion_point:]

# <body>タグの直後にUIコードを挿入
insertion_point = html_content.find('<body>') + len('<body>')
modified_html_content = html_content[:insertion_point] + app_ui_elements + html_content[insertion_point:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(modified_html_content)

print(f"\n処理が完了しました！全{df.shape[0]}店舗の情報を地図に組み込みました。")
print("新機能: 地図上の任意の場所をクリックすると、そこが現在地(基準点)となり、詳細リストが更新されます。")

# --- 生成したHTMLをアプリのウィンドウで開く ---
webview.create_window(
    f"SMAP - Supermarket Map App (全{df.shape[0]}店舗)", 
    file_path,               
    width=1200, height=800,  
    resizable=True           
)
webview.start()