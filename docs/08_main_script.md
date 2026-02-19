# 08. メイン実行スクリプト

## 概要
各モジュールを統合し、投稿処理を一括実行するメインスクリプトを実装する。

## タスク一覧

### メイン処理フロー
- [x] 投稿対象商品の選択
- [x] 画像のホスティング
- [x] 投稿文の生成
- [x] TikTokへの投稿
- [x] 結果のログ記録

### エラーハンドリング
- [x] 各ステップの例外処理
- [x] 失敗時のリカバリー
- [x] 通知機能（オプション）

### ログ出力
- [x] 実行ログの記録
- [x] エラーログの記録
- [x] 統計情報の出力

## main.py の実装

### 実行フロー

```
1. 初期化
   ├── 設定読み込み
   ├── DB接続
   └── API接続確認

2. 商品選択
   └── product_manager.get_next_product_for_posting()

3. 画像準備
   └── image_host.get_hosted_url(product.image_url)

4. 投稿文生成
   └── ai_writer.generate_post_text(product)

5. TikTok投稿
   └── tiktok_poster.post_product(product, text, image_url)

6. 結果記録
   ├── db_manager.add_post_log()
   └── db_manager.update_product() (last_posted_at更新)

7. クリーンアップ
   └── image_host.cleanup_temp_images()
```

### 関数一覧
- [x] `main()` - メイン処理
- [x] `run_single_post()` - 1回の投稿処理
- [x] `validate_api_connections()` - API接続確認
- [x] `log_result(result)` - 結果ログ記録
- [x] `send_notification(message)` - 通知送信（オプション）

### ログ出力例
```
2025-01-15 08:00:01 [INFO] main: === 投稿処理開始: 2025-01-15 08:00:01 ===
2025-01-15 08:00:01 [INFO] main: 商品選択: ポータブルネックファン
2025-01-15 08:00:03 [INFO] main: 画像ホスティング完了: https://i.ibb.co/xxx/image.jpg
2025-01-15 08:00:05 [INFO] main: 投稿文生成完了: 280文字
2025-01-15 08:00:08 [INFO] main: TikTok投稿完了: publish_id=7xxxxxxxxxx
2025-01-15 08:00:08 [INFO] main: === 投稿処理完了 ===
```

## CLI引数

```bash
python main.py              # 通常実行（1投稿）
python main.py --dry-run    # ドライラン（投稿しない）
python main.py --product-id xxx  # 指定商品を投稿
python main.py --init-db    # データベース初期化
```

- [x] argparseでCLI引数対応
- [x] ドライランモード実装

## 完了条件
- [x] `python main.py` で1投稿が完了する
- [x] 全ステップのログが出力される
- [x] エラー時も適切にログが残る
- [x] DBに投稿ログが記録される

## 関連ファイル
- `main.py`
- 全モジュール（依存）
- `logs/cron.log`

## 備考
- cronから実行されるため、絶対パスを使用
- 環境変数はcron実行時にも読み込めるよう設定
- エラー時は次回実行で再試行される
