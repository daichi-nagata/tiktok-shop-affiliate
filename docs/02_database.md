# 02. データベース設計・実装

## 概要
SQLiteデータベースの設計と管理機能を実装する。

## タスク一覧

### テーブル設計
- [x] productsテーブル（商品情報）
- [x] postsテーブル（投稿ログ）
- [x] research_logsテーブル（AIリサーチログ）

### db_manager.py の実装
- [x] データベース接続・初期化
- [x] テーブル作成関数
- [x] CRUD操作の実装

## データベーススキーマ

### products テーブル
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT UNIQUE NOT NULL,        -- 商品ID（URLから抽出）
    item_name TEXT NOT NULL,              -- 商品名
    price INTEGER,                        -- 価格
    image_url TEXT,                       -- 商品画像URL
    category TEXT,                        -- カテゴリ
    description TEXT,                     -- 商品説明
    affiliate_url TEXT,                   -- アフィリエイトURL
    last_posted_at DATETIME,             -- 最終投稿日時
    post_count INTEGER DEFAULT 0,        -- 投稿回数
    is_active BOOLEAN DEFAULT 1,         -- 有効フラグ
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### posts テーブル
```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,                -- 商品ID
    post_text TEXT,                       -- 投稿した本文
    hosted_image_url TEXT,               -- imgBBにアップした画像URL
    tiktok_publish_id TEXT,              -- TikTokのpublish_id
    status TEXT DEFAULT 'pending',       -- pending/published/failed
    posted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES products(item_id)
);
```

### research_logs テーブル
```sql
CREATE TABLE research_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    research_date DATE NOT NULL,
    recommendations TEXT,                -- JSON形式のおすすめリスト
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 実装する関数

### 初期化
- [x] `init_database()` - DB初期化・テーブル作成

### 商品管理
- [x] `add_product(product_data)` - 商品追加
- [x] `get_product(item_id)` - 商品取得
- [x] `get_products_for_posting()` - 投稿対象商品取得（ローテーション）
- [x] `update_product(item_id, data)` - 商品更新
- [x] `deactivate_product(item_id)` - 商品無効化

### 投稿ログ
- [x] `add_post_log(post_data)` - 投稿ログ追加
- [x] `get_recent_posts(limit)` - 最近の投稿取得
- [x] `update_post_status(post_id, status)` - ステータス更新

### リサーチログ
- [x] `add_research_log(recommendations)` - リサーチログ追加
- [x] `get_latest_research()` - 最新リサーチ取得

## 完了条件
- [x] `python -c "from db_manager import init_database; init_database()"` が成功
- [x] 全テーブルが正しく作成される
- [x] CRUD操作がエラーなく動作する

## 関連ファイル
- `db_manager.py`
- `data/posts.db`

## 備考
- SQLiteはファイルベースなのでバックアップが容易
- 商品ローテーションは last_posted_at と post_count を使用
