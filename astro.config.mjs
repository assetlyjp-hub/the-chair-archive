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
});
