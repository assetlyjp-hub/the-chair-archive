#!/usr/bin/env python3
"""
generate-articles.py - Claude API を使って記事を自動生成するスクリプト

使い方:
  python scripts/generate-articles.py --type usecase --limit 2
  python scripts/generate-articles.py --type comparison --dry-run
  python scripts/generate-articles.py --type all --limit 1

オプション:
  --type    記事タイプ（usecase/style/price/designer/comparison/story/all）
  --limit   生成する記事数（デフォルト: 1）
  --dry-run 実際にはファイルを作成せず、プロンプトだけ表示
"""

import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# === 設定 ===
# プロジェクトのルートディレクトリを取得
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "src" / "data"
ARTICLES_DIR = PROJECT_ROOT / "src" / "content" / "articles"

def load_data():
    """椅子・デザイナー・キーワードのデータを読み込む"""
    with open(DATA_DIR / "chairs.json", "r", encoding="utf-8") as f:
        chairs = json.load(f)
    with open(DATA_DIR / "designers.json", "r", encoding="utf-8") as f:
        designers = json.load(f)
    with open(DATA_DIR / "keywords.json", "r", encoding="utf-8") as f:
        keywords = json.load(f)
    return chairs, designers, keywords


def build_prompt(article_type: str, keyword_data: dict, chairs: list, designers: list) -> str:
    """記事タイプに応じたプロンプトを生成する"""

    # 椅子データのサマリーを作成
    chairs_summary = "\n".join([
        f"- {c['name']} ({c['nameJa']}): {c['designer']}, {c['year']}年, {c['style']}, ¥{c['priceRange']['authentic']:,}"
        for c in chairs
    ])

    # 共通の指示
    base_instructions = f"""
あなたは名作椅子の専門ライターです。
以下のデータを参照して、SEOに強く、読者にとって有益な記事を日本語で書いてください。

# 利用可能な椅子データ:
{chairs_summary}

# 記事の要件:
- Markdownフォーマットで出力
- フロントマターを含める（title, description, category, tags, publishedAt, relatedChairs, articleType）
- publishedAt は今日の日付 ({datetime.now().strftime('%Y-%m-%d')})
- 見出し（h2, h3）を適切に使う
- 各セクションに具体的なスペック情報を含める
- 読みやすく、初心者にも分かりやすい文体
- 1500〜2500文字程度
"""

    # 記事タイプ別の指示
    type_instructions = {
        "usecase": f"""
# 記事テーマ: {keyword_data.get('title', '')}
# カテゴリ: usecase
# 記事タイプ: guide

{keyword_data.get('description', '')}に関する記事を書いてください。
用途に合った椅子を5脚程度選び、それぞれの特徴と適性を解説してください。
""",
        "style": f"""
# 記事テーマ: {keyword_data.get('title', '')}
# カテゴリ: style
# 記事タイプ: guide

{keyword_data.get('description', '')}に関する入門ガイドを書いてください。
そのスタイルの歴史的背景、特徴、代表的な椅子を紹介してください。
""",
        "price": f"""
# 記事テーマ: {keyword_data.get('title', '')}
# カテゴリ: price
# 記事タイプ: guide

{keyword_data.get('description', '')}に関する記事を書いてください。
該当する価格帯の椅子をリストアップし、コストパフォーマンスの観点から解説してください。
""",
        "designer": f"""
# 記事テーマ: {keyword_data.get('title', '')}
# カテゴリ: designer
# 記事タイプ: feature

デザイナーの経歴と代表作を詳しく紹介する特集記事を書いてください。
デザイン哲学、時代背景、影響を受けたものなども含めてください。
""",
        "comparison": f"""
# 記事テーマ: {keyword_data.get('title', '')}
# カテゴリ: comparison
# 記事タイプ: comparison

椅子の比較記事を書いてください。
デザイン、座り心地、価格、メンテナンス性などの観点から客観的に比較してください。
最後に「こういう人にはこちらがおすすめ」というアドバイスを含めてください。
""",
        "story": f"""
# 記事テーマ: {keyword_data.get('title', '')}
# カテゴリ: story
# 記事タイプ: story

名作椅子にまつわるストーリーや歴史を語る読み物記事を書いてください。
エピソードや逸話を交えて、読者が椅子に愛着を持てるような内容にしてください。
""",
    }

    return base_instructions + type_instructions.get(article_type, "")


def generate_article_with_claude(prompt: str) -> str:
    """Claude APIを使って記事を生成する"""
    try:
        import anthropic
    except ImportError:
        print("エラー: anthropic パッケージがインストールされていません")
        print("  pip install anthropic")
        sys.exit(1)

    # APIキーの確認
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("エラー: ANTHROPIC_API_KEY 環境変数が設定されていません")
        sys.exit(1)

    # Claude APIを呼び出し
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text


def save_article(content: str, slug: str):
    """記事をファイルに保存する"""
    filepath = ARTICLES_DIR / f"{slug}.md"

    # すでに存在する場合はスキップ
    if filepath.exists():
        print(f"  スキップ: {filepath} はすでに存在します")
        return False

    # ディレクトリがなければ作成
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  保存: {filepath}")
    return True


def main():
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="Claude APIで名作椅子の記事を自動生成")
    parser.add_argument("--type", choices=["usecase", "style", "price", "designer", "comparison", "story", "all"],
                        default="usecase", help="記事タイプ（デフォルト: usecase）")
    parser.add_argument("--limit", type=int, default=1, help="生成する記事数（デフォルト: 1）")
    parser.add_argument("--dry-run", action="store_true", help="ファイルを作成せずプロンプトだけ表示")
    args = parser.parse_args()

    # データ読み込み
    chairs, designers, keywords = load_data()

    # 記事タイプの一覧を取得
    if args.type == "all":
        # 全タイプから均等に選択
        article_types = ["usecase", "style", "price", "designer", "comparison", "story"]
    else:
        article_types = [args.type]

    generated = 0
    for article_type in article_types:
        if generated >= args.limit:
            break

        keyword_list = keywords.get(article_type, [])
        for kw in keyword_list:
            if generated >= args.limit:
                break

            slug = kw.get("slug", "")
            title = kw.get("title", "")

            # すでに存在する記事はスキップ
            if (ARTICLES_DIR / f"{slug}.md").exists():
                continue

            print(f"\n記事生成中: [{article_type}] {title}")

            # プロンプトを生成
            prompt = build_prompt(article_type, kw, chairs, designers)

            if args.dry_run:
                print("--- プロンプト ---")
                print(prompt[:500] + "...")
                print("--- ここまで ---")
                generated += 1
                continue

            # Claude APIで記事生成
            try:
                content = generate_article_with_claude(prompt)
                if save_article(content, slug):
                    generated += 1
            except Exception as e:
                print(f"  エラー: {e}")

    print(f"\n完了: {generated}本の記事を生成しました")


if __name__ == "__main__":
    main()
