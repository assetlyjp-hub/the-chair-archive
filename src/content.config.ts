// content.config.ts - Astro v6 Content Layer API の設定
// glob loader を使って Markdown 記事を読み込む

import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// Magazine記事コレクションの定義
const articles = defineCollection({
  // glob loader で src/content/articles/ 内の .md ファイルを読み込む
  loader: glob({ pattern: '**/*.md', base: './src/content/articles' }),

  // 記事のフロントマターのスキーマ（バリデーション）
  schema: z.object({
    title: z.string(),                    // 記事タイトル
    description: z.string(),              // 概要（SEO用）
    category: z.enum([                    // 記事カテゴリ
      'usecase',      // 用途別おすすめ
      'style',        // スタイル別
      'price',        // 価格帯別
      'designer',     // デザイナー特集
      'comparison',   // 比較記事
      'story',        // 歴史・ストーリー
    ]),
    tags: z.array(z.string()).optional(), // タグ（任意）
    publishedAt: z.string(),             // 公開日（YYYY-MM-DD）
    updatedAt: z.string().optional(),    // 更新日（任意）
    relatedChairs: z.array(z.string()).optional(), // 関連する椅子のID
    articleType: z.enum([                // 記事タイプ
      'guide',       // ガイド
      'feature',     // 特集
      'comparison',  // 比較
      'story',       // ストーリー
    ]),
  }),
});

// コレクションをエクスポート
export const collections = { articles };
