"""
TikTok投稿機能
TikTok Content Posting APIでフォト投稿を行う
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

from config import (
    TIKTOK_CLIENT_KEY,
    TIKTOK_CLIENT_SECRET,
    TIKTOK_ACCESS_TOKEN,
    TIKTOK_API_BASE_URL,
    TIKTOK_AUTH_URL,
    TOKENS_FILE_PATH,
    DATA_DIR,
)

logger = logging.getLogger(__name__)

# API エンドポイント
CONTENT_INIT_URL = f"{TIKTOK_API_BASE_URL}/v2/post/publish/content/init/"
STATUS_FETCH_URL = f"{TIKTOK_API_BASE_URL}/v2/post/publish/status/fetch/"
TOKEN_URL = f"{TIKTOK_API_BASE_URL}/v2/oauth/token/"

# 投稿ステータス
STATUS_PROCESSING_UPLOAD = "PROCESSING_UPLOAD"
STATUS_PROCESSING_DOWNLOAD = "PROCESSING_DOWNLOAD"
STATUS_SEND_TO_USER_INBOX = "SEND_TO_USER_INBOX"
STATUS_PUBLISH_COMPLETE = "PUBLISH_COMPLETE"
STATUS_FAILED = "FAILED"


class TikTokTokenManager:
    """TikTokのアクセストークン管理"""

    def __init__(self, tokens_file: Path = None):
        self.tokens_file = tokens_file or TOKENS_FILE_PATH
        self._tokens = None

    def load_tokens(self) -> Optional[dict]:
        """トークンをファイルから読み込み"""
        try:
            if self.tokens_file.exists():
                with open(self.tokens_file, "r") as f:
                    self._tokens = json.load(f)
                    return self._tokens
        except Exception as e:
            logger.error(f"トークン読み込みエラー: {e}")
        return None

    def save_tokens(self, tokens: dict) -> bool:
        """トークンをファイルに保存"""
        try:
            self.tokens_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.tokens_file, "w") as f:
                json.dump(tokens, f, indent=2)
            self._tokens = tokens
            logger.info("トークンを保存しました")
            return True
        except Exception as e:
            logger.error(f"トークン保存エラー: {e}")
            return False

    def get_access_token(self) -> Optional[str]:
        """有効なアクセストークンを取得"""
        # 環境変数から直接取得
        if TIKTOK_ACCESS_TOKEN:
            return TIKTOK_ACCESS_TOKEN

        # ファイルから読み込み
        tokens = self.load_tokens()
        if not tokens:
            logger.warning("トークンが設定されていません")
            return None

        # 有効期限チェック
        expires_at = tokens.get("expires_at")
        if expires_at:
            expires_time = datetime.fromisoformat(expires_at)
            if datetime.now() > expires_time:
                logger.info("トークンの有効期限が切れています。更新を試みます...")
                if self.refresh_access_token():
                    return self._tokens.get("access_token")
                return None

        return tokens.get("access_token")

    def refresh_access_token(self) -> bool:
        """リフレッシュトークンでアクセストークンを更新"""
        tokens = self._tokens or self.load_tokens()
        if not tokens or not tokens.get("refresh_token"):
            logger.error("リフレッシュトークンがありません")
            return False

        try:
            response = requests.post(
                TOKEN_URL,
                data={
                    "client_key": TIKTOK_CLIENT_KEY,
                    "client_secret": TIKTOK_CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "refresh_token": tokens["refresh_token"]
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            if "access_token" in result:
                new_tokens = {
                    "access_token": result["access_token"],
                    "refresh_token": result.get("refresh_token", tokens["refresh_token"]),
                    "expires_at": (datetime.now() + timedelta(seconds=result.get("expires_in", 86400))).isoformat(),
                    "open_id": result.get("open_id", tokens.get("open_id"))
                }
                self.save_tokens(new_tokens)
                logger.info("トークンを更新しました")
                return True

        except Exception as e:
            logger.error(f"トークン更新エラー: {e}")

        return False


class TikTokPoster:
    """TikTok Content Posting API クライアント"""

    def __init__(self):
        self.token_manager = TikTokTokenManager()

    def _get_headers(self) -> Optional[dict]:
        """APIリクエスト用ヘッダーを取得"""
        access_token = self.token_manager.get_access_token()
        if not access_token:
            return None

        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }

    def init_photo_post(
        self,
        image_urls: list[str],
        title: str,
        privacy_level: str = "SELF_ONLY",
        disable_comment: bool = False,
        auto_add_music: bool = True
    ) -> Optional[dict]:
        """
        フォト投稿を初期化

        Args:
            image_urls: 画像URLのリスト（1枚以上）
            title: 投稿タイトル（キャプション）
            privacy_level: 公開設定 (PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, SELF_ONLY)
            disable_comment: コメント無効化
            auto_add_music: 自動音楽追加

        Returns:
            dict: {"publish_id": str} or None
        """
        headers = self._get_headers()
        if not headers:
            logger.error("アクセストークンが取得できません")
            return None

        payload = {
            "post_info": {
                "title": title,
                "privacy_level": privacy_level,
                "disable_comment": disable_comment,
                "auto_add_music": auto_add_music
            },
            "source_info": {
                "source": "PULL_FROM_URL",
                "photo_images": image_urls
            },
            "post_mode": "DIRECT_POST",
            "media_type": "PHOTO"
        }

        try:
            logger.info(f"TikTokフォト投稿を初期化中... (画像数: {len(image_urls)})")

            response = requests.post(
                CONTENT_INIT_URL,
                headers=headers,
                json=payload,
                timeout=60
            )

            result = response.json()
            logger.debug(f"API Response: {result}")

            if response.status_code == 200 and result.get("error", {}).get("code") == "ok":
                publish_id = result.get("data", {}).get("publish_id")
                if publish_id:
                    logger.info(f"投稿初期化成功: publish_id={publish_id}")
                    return {"publish_id": publish_id}

            error_msg = result.get("error", {}).get("message", "Unknown error")
            logger.error(f"投稿初期化失敗: {error_msg}")
            return None

        except requests.RequestException as e:
            logger.error(f"API リクエストエラー: {e}")
            return None

    def check_publish_status(self, publish_id: str) -> Optional[dict]:
        """
        投稿ステータスを確認

        Args:
            publish_id: 投稿ID

        Returns:
            dict: {"status": str, "fail_reason": str} or None
        """
        headers = self._get_headers()
        if not headers:
            return None

        try:
            response = requests.post(
                STATUS_FETCH_URL,
                headers=headers,
                json={"publish_id": publish_id},
                timeout=30
            )

            result = response.json()

            if response.status_code == 200:
                status = result.get("data", {}).get("status")
                fail_reason = result.get("data", {}).get("fail_reason", "")

                logger.info(f"投稿ステータス: {status}")
                return {
                    "status": status,
                    "fail_reason": fail_reason
                }

        except requests.RequestException as e:
            logger.error(f"ステータス確認エラー: {e}")

        return None

    def wait_for_publish(self, publish_id: str, timeout: int = 120, interval: int = 5) -> dict:
        """
        投稿完了を待機

        Args:
            publish_id: 投稿ID
            timeout: タイムアウト秒数
            interval: チェック間隔秒数

        Returns:
            dict: {"success": bool, "status": str, "fail_reason": str}
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            status_result = self.check_publish_status(publish_id)

            if not status_result:
                time.sleep(interval)
                continue

            status = status_result.get("status")

            if status == STATUS_PUBLISH_COMPLETE:
                return {"success": True, "status": status, "fail_reason": ""}

            if status == STATUS_FAILED:
                return {
                    "success": False,
                    "status": status,
                    "fail_reason": status_result.get("fail_reason", "Unknown")
                }

            # まだ処理中
            logger.debug(f"投稿処理中... (status: {status})")
            time.sleep(interval)

        return {"success": False, "status": "TIMEOUT", "fail_reason": "処理がタイムアウトしました"}


def post_product(product: dict, post_text: str, image_url: str) -> Optional[dict]:
    """
    商品を投稿

    Args:
        product: 商品情報
        post_text: 投稿文（本文 + ハッシュタグ）
        image_url: 画像の公開URL

    Returns:
        dict: {"publish_id": str, "success": bool} or None
    """
    poster = TikTokPoster()

    # 投稿初期化
    init_result = poster.init_photo_post(
        image_urls=[image_url],
        title=post_text,
        privacy_level="SELF_ONLY"  # 初期は非公開（審査通過後にPUBLIC_TO_EVERYONEに変更）
    )

    if not init_result:
        logger.error("投稿の初期化に失敗しました")
        return None

    publish_id = init_result["publish_id"]

    # 完了を待機
    result = poster.wait_for_publish(publish_id)

    return {
        "publish_id": publish_id,
        "success": result.get("success", False),
        "status": result.get("status"),
        "fail_reason": result.get("fail_reason", "")
    }


def generate_auth_url(redirect_uri: str, state: str = "random_state") -> str:
    """
    OAuth認証URLを生成

    Args:
        redirect_uri: コールバックURL
        state: CSRFトークン

    Returns:
        str: 認証URL
    """
    params = {
        "client_key": TIKTOK_CLIENT_KEY,
        "scope": "video.publish,video.upload",
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state
    }

    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{TIKTOK_AUTH_URL}?{query_string}"


def exchange_code_for_token(code: str, redirect_uri: str) -> Optional[dict]:
    """
    認証コードをアクセストークンに交換

    Args:
        code: 認証コード
        redirect_uri: コールバックURL

    Returns:
        dict: トークン情報 or None
    """
    try:
        response = requests.post(
            TOKEN_URL,
            data={
                "client_key": TIKTOK_CLIENT_KEY,
                "client_secret": TIKTOK_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            },
            timeout=30
        )

        result = response.json()

        if "access_token" in result:
            tokens = {
                "access_token": result["access_token"],
                "refresh_token": result.get("refresh_token"),
                "expires_at": (datetime.now() + timedelta(seconds=result.get("expires_in", 86400))).isoformat(),
                "open_id": result.get("open_id")
            }

            # 保存
            token_manager = TikTokTokenManager()
            token_manager.save_tokens(tokens)

            logger.info("トークンを取得・保存しました")
            return tokens

    except Exception as e:
        logger.error(f"トークン取得エラー: {e}")

    return None


if __name__ == "__main__":
    from config import setup_logging
    setup_logging()

    print("TikTok Poster テスト")
    print("=" * 50)

    # トークン確認
    token_manager = TikTokTokenManager()
    access_token = token_manager.get_access_token()

    if access_token:
        print(f"アクセストークン: {access_token[:20]}...")
    else:
        print("アクセストークンが設定されていません")
        print("\n認証URLを生成するには:")
        print("  redirect_uri = 'https://your-callback-url.com/callback'")
        print("  auth_url = generate_auth_url(redirect_uri)")
        print("  print(auth_url)")
