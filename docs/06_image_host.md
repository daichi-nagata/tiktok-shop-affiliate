# 06. 画像ホスティング機能

## 概要
商品画像をダウンロードし、imgBB APIを使用して公開URLを取得する。

## タスク一覧

### 画像ダウンロード
- [x] 商品画像URLからのダウンロード
- [x] 画像形式の検証（JPEG, PNG, WebP）
- [x] 一時ファイルとしての保存

### imgBB API連携
- [x] APIキーの設定
- [x] 画像アップロード処理
- [x] 公開URL取得

### 画像処理
- [x] サイズ最適化（必要に応じて）
- [x] フォーマット変換（必要に応じて）
- [x] 一時ファイルのクリーンアップ

## image_host.py の実装

### imgBB API仕様
- エンドポイント: `POST https://api.imgbb.com/1/upload`
- 認証: APIキー（クエリパラメータ）
- 制限: 無料枠あり（月間容量制限）

### 関数一覧
- [x] `download_image(url, save_path)` - 画像ダウンロード
- [x] `validate_image(file_path)` - 画像検証
- [x] `upload_to_imgbb(file_path)` - imgBBアップロード
- [x] `get_hosted_url(image_url)` - ダウンロード→アップロード→URL取得
- [x] `cleanup_temp_images()` - 一時ファイル削除

### APIリクエスト例
```python
import requests
import base64

def upload_to_imgbb(file_path: str) -> str:
    """画像をimgBBにアップロードして公開URLを返す"""
    with open(file_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    response = requests.post(
        "https://api.imgbb.com/1/upload",
        params={"key": IMGBB_API_KEY},
        data={"image": image_data}
    )

    result = response.json()
    if result["success"]:
        return result["data"]["url"]
    else:
        raise Exception(f"Upload failed: {result}")
```

### レスポンス例
```json
{
    "success": true,
    "data": {
        "url": "https://i.ibb.co/xxxxx/image.jpg",
        "display_url": "https://i.ibb.co/xxxxx/image.jpg",
        "delete_url": "https://ibb.co/xxxxx/delete",
        "expiration": "0"
    }
}
```

## 画像保存パス
```
images/
├── temp/                    # 一時ダウンロード用
│   └── {item_id}_{timestamp}.jpg
└── uploaded/                # アップロード済み記録用
    └── {item_id}_hosted.json
```

## エラーハンドリング

- [x] ダウンロード失敗時のリトライ（3回まで）
- [x] アップロード失敗時のログ記録
- [x] 無効な画像フォーマット時の対応
- [x] API制限到達時の処理

## 完了条件
- [x] 商品画像URLからダウンロードできる
- [x] imgBBにアップロードできる
- [x] 公開URLを取得できる
- [x] 一時ファイルが適切にクリーンアップされる

## 関連ファイル
- `image_host.py`
- `images/` ディレクトリ
- `config.py`（IMGBB_API_KEY）

## 備考
- imgBBの無料枠を超える場合は有料プランか代替サービスを検討
- 代替サービス: Imgur, Cloudinary, AWS S3
- 画像は投稿後も削除されない（imgBBの仕様）
