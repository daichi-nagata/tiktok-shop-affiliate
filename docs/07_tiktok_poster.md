# 07. TikTok投稿機能

## 概要
TikTok Content Posting APIを使用してフォト投稿を行う。

## タスク一覧

### OAuth認証
- [x] TikTok Developer Portalでアプリ登録
- [x] OAuth 2.0フローの実装
- [x] アクセストークン取得・更新処理

### フォト投稿
- [x] 画像アップロード（Direct Post方式）
- [x] 投稿文・ハッシュタグの設定
- [x] 投稿結果の確認

### エラーハンドリング
- [x] API制限の監視
- [x] 投稿失敗時のリトライ
- [x] ステータス追跡

## tiktok_poster.py の実装

### TikTok Content Posting API仕様

**エンドポイント**
- 投稿初期化: `POST /v2/post/publish/inbox/video/init/` (フォトにも使用)
- コンテンツ公開: `POST /v2/post/publish/content/init/`
- ステータス確認: `GET /v2/post/publish/status/fetch/`

**認証**
- OAuth 2.0 Authorization Code Flow
- スコープ: `video.publish`, `video.upload`

**制限**
- 1日あたり15フォト投稿/ユーザー
- 未審査クライアントは非公開モードのみ

### 関数一覧
- [x] `get_access_token()` - アクセストークン取得
- [x] `refresh_access_token()` - トークン更新
- [x] `init_photo_post(image_urls)` - 投稿初期化
- [x] `publish_photo(publish_id, text, hashtags)` - フォト公開
- [x] `check_publish_status(publish_id)` - ステータス確認
- [x] `post_product(product, post_text, image_url)` - 商品投稿メイン処理

### OAuth 2.0 フロー

```python
# 1. 認証URLを生成してユーザーにアクセスさせる
AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
params = {
    "client_key": CLIENT_KEY,
    "scope": "video.publish,video.upload",
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "state": random_state
}

# 2. コールバックでcodeを受け取り、アクセストークンを取得
response = requests.post(
    "https://open.tiktokapis.com/v2/oauth/token/",
    data={
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": authorization_code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }
)

# 3. アクセストークンを保存
access_token = response.json()["access_token"]
refresh_token = response.json()["refresh_token"]
```

### フォト投稿フロー

```python
# 1. Direct Post方式でフォト投稿を初期化
response = requests.post(
    "https://open.tiktokapis.com/v2/post/publish/content/init/",
    headers={"Authorization": f"Bearer {access_token}"},
    json={
        "post_info": {
            "title": post_text,
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_comment": False,
            "auto_add_music": True
        },
        "source_info": {
            "source": "PULL_FROM_URL",
            "photo_images": [image_url]
        },
        "post_mode": "DIRECT_POST",
        "media_type": "PHOTO"
    }
)

publish_id = response.json()["data"]["publish_id"]

# 2. ステータス確認
status_response = requests.post(
    "https://open.tiktokapis.com/v2/post/publish/status/fetch/",
    headers={"Authorization": f"Bearer {access_token}"},
    json={"publish_id": publish_id}
)
```

## トークン管理

### 保存場所
```
data/
└── tiktok_tokens.json
```

### ファイル形式
```json
{
    "access_token": "xxx",
    "refresh_token": "xxx",
    "expires_at": "2025-01-20T12:00:00",
    "open_id": "xxx"
}
```

- [x] トークン保存処理
- [x] トークン読み込み処理
- [x] 有効期限チェック・自動更新

## 投稿ステータス管理

| status | 説明 |
|--------|------|
| PROCESSING_UPLOAD | アップロード処理中 |
| PROCESSING_DOWNLOAD | ダウンロード処理中 |
| SEND_TO_USER_INBOX | 受信箱に送信済み |
| PUBLISH_COMPLETE | 公開完了 |
| FAILED | 失敗 |

## 完了条件
- [x] OAuth認証でアクセストークンを取得できる
- [x] フォト投稿が成功する
- [x] 投稿ステータスを確認できる
- [x] トークンの自動更新が動作する

## 関連ファイル
- `tiktok_poster.py`
- `data/tiktok_tokens.json`
- `config.py`（CLIENT_KEY, CLIENT_SECRET）

## 備考
- TikTok APIの審査通過前は非公開モードのみ
- 審査通過後に公開投稿が可能
- ショッピングタグ追加は手動対応が必要
