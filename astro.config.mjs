// @ts-check
// Astro設定ファイル - サイトマップとMDXの統合を設定
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import mdx from '@astrojs/mdx';

export default defineConfig({
  // 本番サイトのURL
  site: 'https://thechairarchive.com',
  // 使用するインテグレーション
  integrations: [
    sitemap(),  // サイトマップ自動生成
    mdx(),      // MDXファイルサポート
  ],
  // 多言語（i18n）設定
  i18n: {
    defaultLocale: 'ja',       // デフォルト言語: 日本語
    locales: ['ja', 'en'],     // 対応言語: 日本語 と 英語
    routing: {
      prefixDefaultLocale: false,  // 日本語は / のまま、英語は /en/ プレフィックス
    },
  },
});
