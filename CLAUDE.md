# TikTok Shop アフィリエイト自動投稿システム

## プロジェクト概要

TikTok Shopの商品を、AIリサーチ → 自動投稿するシステム。
Claude APIでSNS上の売れ筋商品を調査し、投稿文を自動生成、TikTok Content Posting APIでフォト投稿を行う。

## 技術スタック

- **言語**: Python 3.11+
- **AI**: Claude API (claude-sonnet-4-5-20250929)
- **投稿先**: TikTok Content Posting API
- **画像ホスティング**: imgBB API
- **データベース**: SQLite
- **スクレイピング**: requests + BeautifulSoup

## ディレクトリ構成

```
tiktok-shop-affiliate/
├── main.py              # メイン実行スクリプト（投稿処理）
├── researcher.py        # AIリサーチ（売れ筋商品調査）
├── product_manager.py   # 商品管理（URL→スクレイピング→DB登録）
├── ai_writer.py         # Claude APIで投稿文生成
├── tiktok_poster.py     # TikTok Content Posting API連携
├── image_host.py        # imgBB画像ホスティング
├── db_manager.py        # SQLiteデータベース操作
├── config.py            # 設定・APIキー管理
├── .env                 # 環境変数（APIキー等）※Git管理外
├── requirements.txt     # Pythonパッケージ
├── data/
│   ├── posts.db         # SQLiteデータベース
│   └── urls.txt         # 商品URLリスト（手動入力）
├── images/              # ダウンロードした商品画像（一時保存）
├── logs/
│   └── cron.log         # 実行ログ
└── docs/                # 開発チケット
```

## 主要機能

### 1. AIリサーチ機能 (researcher.py)
- Claude APIのWeb検索ツールでSNSトレンドを調査
- おすすめ商品リストを出力（商品名・推定価格帯・おすすめ理由・検索キーワード）
- 週1回実行

### 2. 商品管理機能 (product_manager.py)
- urls.txtから商品URLを読み込み
- TikTok Shop商品ページをスクレイピング
- 商品情報（名前、価格、画像URL、カテゴリ、説明文）をDB登録

### 3. 投稿文生成機能 (ai_writer.py)
- Claude APIで商品紹介文を自動生成
- 300文字以内、絵文字3〜5個、PR表記必須
- 関連ハッシュタグ5〜7個を生成

### 4. 画像ホスティング機能 (image_host.py)
- 商品画像をダウンロード
- imgBB APIで公開URLを取得

### 5. TikTok投稿機能 (tiktok_poster.py)
- TikTok Content Posting APIでフォト投稿
- 1日3回（8:00, 14:00, 20:00）自動投稿

### 6. データベース管理 (db_manager.py)
- products: 商品情報
- posts: 投稿ログ
- research_logs: AIリサーチログ

## 環境変数 (.env)

```
ANTHROPIC_API_KEY=your_claude_api_key
TIKTOK_CLIENT_KEY=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret
TIKTOK_ACCESS_TOKEN=your_tiktok_access_token
IMGBB_API_KEY=your_imgbb_api_key
```

## 自動実行スケジュール

| 処理 | 頻度 | 時刻 |
|------|------|------|
| AIリサーチ | 週1回 | 月曜 7:00 |
| 投稿 | 1日3回 | 8:00, 14:00, 20:00 |

## 開発チケット

チケットは `docs/` フォルダで管理:
- 01_setup.md - 環境構築・初期設定
- 02_database.md - データベース設計・実装
- 03_product_manager.md - 商品管理機能
- 04_ai_researcher.md - AIリサーチ機能
- 05_ai_writer.md - 投稿文生成機能
- 06_image_host.md - 画像ホスティング機能
- 07_tiktok_poster.md - TikTok投稿機能
- 08_main_script.md - メイン実行スクリプト
- 09_scheduler.md - 自動実行設定

## 注意事項

- **ステマ規制**: 投稿文に「PR」を必ず含める
- **AI生成コンテンツラベル**: TikTok投稿時にトグルをONにする
- **TikTok API審査**: 未審査クライアントは非公開モード
- **レート制限**: 1日15フォト投稿/ユーザーまで

## 月間コスト見積もり

| 項目 | 費用 |
|------|------|
| Claude API | 約200〜400円 |
| TikTok Content Posting API | 無料 |
| imgBB | 無料 |
| **合計** | **約200〜400円/月** |
