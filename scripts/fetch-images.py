"""
楽天API 椅子画像取得スクリプト
================================
楽天市場APIで椅子を検索し、商品画像をダウンロード＆
chairs.json のアフィリエイトURLを更新する。

使い方:
  python scripts/fetch-images.py
  python scripts/fetch-images.py --dry-run  # 画像DLせず確認のみ
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

# Windows の文字コード問題を回避
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# === 設定 ===
# 楽天APIの認証情報
APP_ID = "33f9e64b-57b8-4ebb-9c2c-00fb0126a84b"
AFFILIATE_ID = "52758c3e.fdf645ec.52758c3f.5519e6eb"

# パス設定
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CHAIRS_JSON = PROJECT_DIR / "src" / "data" / "chairs.json"
IMAGES_DIR = PROJECT_DIR / "public" / "images" / "chairs"

# 楽天市場商品検索API のURL（2026年新仕様）
RAKUTEN_API_URL = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20220601"
# アクセスキー（2026年新仕様で必須）
ACCESS_KEY = "pk_R6pUxXgdzwSc02b4XMJeO2naxmHFwzv9bHgROdleaCY"

# === 椅子の検索キーワード（日本語名で検索する） ===
# chairs.json の nameJa をそのまま使うと検索精度が低いことがあるので
# 専用の検索キーワードを定義
SEARCH_KEYWORDS = {
    "eames-shell-dsw": "ハーマンミラー イームズ シェルチェア DSW",
    "wishbone-ch24": "カールハンセン CH24 Yチェア",
    "barcelona-chair": "バルセロナチェア ミース",
    "eames-lounge": "ハーマンミラー イームズ ラウンジチェア",
    "series7-3107": "フリッツハンセン セブンチェア 3107",
    "tulip-chair": "チューリップチェア サーリネン",
    "panton-chair": "ヴィトラ パントンチェア",
    "the-chair-pp501": "ウェグナー ザチェア PP501",
    "swan-chair": "フリッツハンセン スワンチェア",
    "egg-chair": "フリッツハンセン エッグチェア",
    "lc2": "LC2 コルビュジエ 1人掛け アームチェア",
    "wassily-b3": "ワシリーチェア マルセル ブロイヤー",
    "diamond-chair": "ベルトイア ダイヤモンドチェア",
    "ball-chair": "ボールチェア エーロ アールニオ",
    "superleggera": "スーパーレジェーラ カッシーナ チェア",
    "stool-60": "アルテック スツール60",
    "ch07-shell": "カールハンセン CH07 シェルチェア",
    "eames-daw": "ハーマンミラー イームズ DAW",
    "ant-chair-3100": "フリッツハンセン アリンコチェア",
    "thonet-no14": "トーネット 214 曲木 チェア",
    "colonial-ow149": "カールハンセン コロニアルチェア OW149",
}


def search_rakuten(keyword, hits=3):
    """
    楽天市場で商品を検索する

    Parameters:
        keyword: 検索キーワード
        hits: 取得件数（最大30）

    Returns:
        検索結果のJSON（辞書型）
    """
    # APIリクエストのパラメータを組み立てる
    params = {
        "applicationId": APP_ID,
        "accessKey": ACCESS_KEY,
        "affiliateId": AFFILIATE_ID,
        "keyword": keyword,
        "hits": hits,
        "imageFlag": 1,           # 画像ありの商品のみ
        "sort": "-itemPrice",  # 価格高い順（正規品を優先するため）
    }

    # URLを組み立ててリクエスト
    url = f"{RAKUTEN_API_URL}?{urllib.parse.urlencode(params)}"

    try:
        # 新仕様ではOriginヘッダーが必要
        req = urllib.request.Request(url)
        req.add_header("Origin", "https://thechairarchive.com")
        req.add_header("Referer", "https://thechairarchive.com/")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except Exception as e:
        print(f"  ❌ API エラー: {e}")
        return None


def download_image(url, save_path):
    """
    画像をダウンロードして保存する

    Parameters:
        url: 画像のURL
        save_path: 保存先パス
    """
    try:
        urllib.request.urlretrieve(url, save_path)
        return True
    except Exception as e:
        print(f"  ❌ 画像ダウンロードエラー: {e}")
        return False


def get_large_image_url(image_urls):
    """
    楽天の画像URLから大きいサイズのURLを取得する
    楽天の画像URLは ?_ex=128x128 のようなサイズ指定がある
    これを 600x600 に変更する
    """
    if not image_urls:
        return None

    # 最初の画像URLを取得
    url = image_urls[0].get("imageUrl", "")

    if not url:
        return None

    # サイズを大きくする（128x128 → 600x600）
    url = url.replace("?_ex=128x128", "?_ex=600x600")
    url = url.replace("?_ex=64x64", "?_ex=600x600")

    return url


def main():
    # コマンドライン引数チェック
    dry_run = "--dry-run" in sys.argv

    # 画像保存フォルダを作成
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # chairs.json を読み込む
    with open(CHAIRS_JSON, "r", encoding="utf-8") as f:
        chairs = json.load(f)

    print(f"=== 楽天API 椅子画像取得 ===")
    print(f"対象: {len(chairs)}脚")
    if dry_run:
        print("(dry-run モード: 画像はダウンロードしません)\n")
    else:
        print()

    # 更新カウンター
    updated = 0
    skipped = 0
    failed = 0

    for chair in chairs:
        chair_id = chair["id"]
        chair_name = chair["nameJa"]

        # 既に画像がある場合はスキップ
        image_path = IMAGES_DIR / f"{chair_id}.jpg"
        if image_path.exists() and not dry_run:
            print(f"⏭ {chair_name} — 画像あり（スキップ）")
            skipped += 1
            continue

        # 検索キーワードを取得
        keyword = SEARCH_KEYWORDS.get(chair_id, chair_name)
        print(f"🔍 {chair_name} — 検索中: 「{keyword}」")

        # 楽天APIで検索
        result = search_rakuten(keyword)

        if not result or not result.get("Items"):
            print(f"  ❌ 商品が見つかりませんでした")
            failed += 1
            # APIレート制限対策（1秒に1回まで）
            time.sleep(1)
            continue

        # 最初の商品を使用
        item = result["Items"][0]["Item"]
        item_name = item.get("itemName", "不明")
        item_price = item.get("itemPrice", 0)
        item_url = item.get("affiliateUrl", "") or item.get("itemUrl", "")
        image_url = get_large_image_url(item.get("mediumImageUrls", []))

        print(f"  ✅ 商品: {item_name[:50]}...")
        print(f"     価格: ¥{item_price:,}")
        print(f"     画像: {image_url}")
        print(f"     リンク: {item_url[:60]}...")

        if not dry_run:
            # 画像をダウンロード
            if image_url and download_image(image_url, image_path):
                print(f"  💾 保存: {image_path.name}")

                # chairs.json の楽天アフィリエイトURLを更新
                chair["affiliateUrls"]["rakuten"] = item_url
                updated += 1
            else:
                failed += 1
        else:
            updated += 1

        # APIレート制限対策（1秒に1回まで）
        time.sleep(1)

    # chairs.json を保存（dry-run でなければ）
    if not dry_run and updated > 0:
        with open(CHAIRS_JSON, "w", encoding="utf-8") as f:
            json.dump(chairs, f, ensure_ascii=False, indent=2)
        print(f"\n📝 chairs.json を更新しました")

    # 結果サマリー
    print(f"\n=== 完了 ===")
    print(f"✅ 更新: {updated}脚")
    print(f"⏭ スキップ: {skipped}脚")
    print(f"❌ 失敗: {failed}脚")


if __name__ == "__main__":
    main()
