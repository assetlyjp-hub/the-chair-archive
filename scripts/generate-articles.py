#!/usr/bin/env python3
"""
generate-articles.py - Claude API を使って記事を自動生成するスクリプト

使い方:
  python scripts/generate-articles.py --type usecase --limit 2
  python scripts/generate-articles.py --type comparison --dry-run
  python scripts/generate-articles.py --type all --limit 1
  python scripts/generate-articles.py --type usecase --limit 2 --lang en

オプション:
  --type    記事タイプ（usecase/style/price/designer/comparison/story/all）
  --limit   生成する記事数（デフォルト: 1）
  --dry-run 実際にはファイルを作成せず、プロンプトだけ表示
  --lang    言語（ja/en、デフォルト: ja）
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
# 英語記事の保存先ディレクトリ
ARTICLES_DIR_EN = PROJECT_ROOT / "src" / "content" / "articles" / "en"

def load_data():
    """椅子・デザイナー・キーワードのデータを読み込む"""
    with open(DATA_DIR / "chairs.json", "r", encoding="utf-8") as f:
        chairs = json.load(f)
    with open(DATA_DIR / "designers.json", "r", encoding="utf-8") as f:
        designers = json.load(f)
    with open(DATA_DIR / "keywords.json", "r", encoding="utf-8") as f:
        keywords = json.load(f)
    return chairs, designers, keywords


def build_prompt(article_type: str, keyword_data: dict, chairs: list, designers: list, lang: str = "ja") -> str:
    """記事タイプに応じたプロンプトを生成する

    Args:
        article_type: 記事の種類（usecase, style, price, designer, comparison, story）
        keyword_data: キーワードデータ（title, slug, description など）
        chairs: 椅子データのリスト
        designers: デザイナーデータのリスト
        lang: 言語コード（'ja' = 日本語, 'en' = 英語）
    """

    # 椅子データのサマリーを作成
    chairs_summary = "\n".join([
        f"- {c['name']} ({c['nameJa']}): {c['designer']}, {c['year']}年, {c['style']}, ¥{c['priceRange']['authentic']:,}"
        for c in chairs
    ])

    # 言語に応じた共通の指示を切り替え
    if lang == "en":
        # === 英語版の指示 ===
        base_instructions = f"""
You are an expert writer specializing in iconic designer chairs.
Using the data below, write an SEO-friendly, informative article in English.

# Available chair data:
{chairs_summary}

# Article requirements:
- Output in Markdown format
- Include frontmatter (title, description, category, tags, publishedAt, relatedChairs, articleType)
- publishedAt should be today's date ({datetime.now().strftime('%Y-%m-%d')})
- Use headings (h2, h3) appropriately
- Include specific specs and dimensions in each section
- Write in a clear, engaging style accessible to design enthusiasts
- Aim for 800-1500 words
"""
    else:
        # === 日本語版の指示（既存のまま） ===
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

    # 記事タイプ別の指示（言語に応じて切り替え）
    if lang == "en":
        # === 英語版の記事タイプ別指示 ===
        type_instructions = {
            "usecase": f"""
# Article theme: {keyword_data.get('title', '')}
# Category: usecase
# Article type: guide

Write an article about {keyword_data.get('description', '')}.
Select around 5 chairs suited to this use case and explain each one's features and suitability.
""",
            "style": f"""
# Article theme: {keyword_data.get('title', '')}
# Category: style
# Article type: guide

Write a beginner's guide about {keyword_data.get('description', '')}.
Cover the historical background, defining characteristics, and representative chairs of this style.
""",
            "price": f"""
# Article theme: {keyword_data.get('title', '')}
# Category: price
# Article type: guide

Write an article about {keyword_data.get('description', '')}.
List chairs in the relevant price range and analyze them from a value-for-money perspective.
""",
            "designer": f"""
# Article theme: {keyword_data.get('title', '')}
# Category: designer
# Article type: feature

Write a feature article profiling the designer's career and major works.
Include their design philosophy, historical context, and influences.
""",
            "comparison": f"""
# Article theme: {keyword_data.get('title', '')}
# Category: comparison
# Article type: comparison

Write a chair comparison article.
Compare objectively across design, comfort, price, and maintenance.
End with 'this chair is for you if...' style recommendations.
""",
            "story": f"""
# Article theme: {keyword_data.get('title', '')}
# Category: story
# Article type: story

Write a narrative article about the stories and history behind iconic chairs.
Include anecdotes and episodes that help readers develop an emotional connection to the chairs.
""",
        }
    else:
        # === 日本語版の記事タイプ別指示（既存のまま） ===
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


def save_article(content: str, slug: str, lang: str = "ja"):
    """記事をファイルに保存する

    Args:
        content: 記事の内容（Markdown）
        slug: 記事のスラッグ（ファイル名に使用）
        lang: 言語コード（'ja' = 日本語, 'en' = 英語）
    """
    # 言語に応じて保存先を切り替え
    if lang == "en":
        filepath = ARTICLES_DIR_EN / f"{slug}.md"
    else:
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
    parser.add_argument("--lang", choices=["ja", "en"], default="ja",
                        help="記事の言語（デフォルト: ja）。en を指定すると英語記事を生成")
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

            # すでに存在する記事はスキップ（言語に応じたディレクトリを確認）
            check_dir = ARTICLES_DIR_EN if args.lang == "en" else ARTICLES_DIR
            if (check_dir / f"{slug}.md").exists():
                continue

            print(f"\n記事生成中: [{article_type}] {title}")

            # プロンプトを生成（言語オプションを渡す）
            prompt = build_prompt(article_type, kw, chairs, designers, lang=args.lang)

            if args.dry_run:
                print("--- プロンプト ---")
                print(prompt[:500] + "...")
                print("--- ここまで ---")
                generated += 1
                continue

            # Claude APIで記事生成
            try:
                content = generate_article_with_claude(prompt)
                if save_article(content, slug, lang=args.lang):
                    generated += 1
            except Exception as e:
                print(f"  エラー: {e}")

    print(f"\n完了: {generated}本の記事を生成しました")


if __name__ == "__main__":
    main()
