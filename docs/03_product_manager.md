# 03. 商品管理機能

## 概要
URLリストから商品情報をスクレイピングし、データベースに登録する機能を実装する。

## タスク一覧

### urls.txt 管理
- [x] urls.txtのフォーマット定義
- [x] URLの読み込み処理
- [x] 処理済みURLの管理（重複防止）

### スクレイピング機能
- [x] TikTok Shop商品ページの解析
- [x] 商品情報の抽出（名前、価格、画像、説明）
- [x] エラーハンドリング（取得失敗時の処理）

### データ登録
- [x] 抽出データの検証
- [x] データベースへの登録
- [x] 登録結果のログ出力

## urls.txt フォーマット
```
# 1行1URL、#で始まる行はコメント
https://shop.tiktok.com/view/product/xxxxx1
https://shop.tiktok.com/view/product/xxxxx2
https://shop.tiktok.com/view/product/xxxxx3
```

## product_manager.py の実装

### 関数一覧
- [x] `load_urls_from_file(filepath)` - URLファイル読み込み
- [x] `extract_item_id(url)` - URLから商品IDを抽出
- [x] `scrape_product(url)` - 商品情報スクレイピング
- [x] `validate_product_data(data)` - データ検証
- [x] `register_products_from_urls()` - 一括登録処理
- [x] `get_next_product_for_posting()` - 投稿用商品選択

### スクレイピング対象情報
```python
{
    "item_id": "抽出した商品ID",
    "item_name": "商品名",
    "price": 1980,
    "image_url": "https://...",
    "category": "カテゴリ",
    "description": "商品説明文",
    "affiliate_url": "元のURL"
}
```

### エラーハンドリング
- [x] ネットワークエラー時のリトライ
- [x] ページ構造変更時のフォールバック
- [x] 取得失敗商品のスキップとログ記録

## 商品選択ロジック（ローテーション）

```python
# 投稿対象選択の優先順位
# 1. まだ一度も投稿していない商品
# 2. 投稿回数が少ない商品
# 3. 最終投稿から時間が経っている商品
```

## フォールバック: 手動CSV入力
スクレイピングが不安定な場合のバックアップ

### products.csv フォーマット
```csv
item_id,item_name,price,image_url,category,description,affiliate_url
xxxxx1,商品名A,1980,https://...,美容,説明文,https://...
```

- [x] CSVインポート機能の実装

## 完了条件
- [x] urls.txtから商品情報を取得できる
- [x] 取得した情報がDBに登録される
- [x] 投稿用商品選択が正しく動作する
- [x] エラー時もシステムが停止しない

## 関連ファイル
- `product_manager.py`
- `data/urls.txt`
- `data/products.csv`（フォールバック用）

## 備考
- TikTok ShopのDOM構造は変更される可能性がある
- スクレイピングが困難な場合はCSV入力に切り替え
- レート制限に注意（リクエスト間隔を空ける）
