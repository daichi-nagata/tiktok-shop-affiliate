"""
画像ホスティング機能
商品画像をダウンロードし、imgBB APIで公開URLを取得
"""

import base64
import logging
import os
import time
from pathlib import Path
from typing import Optional

import requests
from PIL import Image

from config import IMGBB_API_KEY, IMGBB_API_URL, IMAGES_DIR

logger = logging.getLogger(__name__)

# 設定
MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# ディレクトリ
TEMP_DIR = IMAGES_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def download_image(url: str, save_path: str = None) -> Optional[str]:
    """
    URLから画像をダウンロード

    Args:
        url: 画像URL
        save_path: 保存パス（指定しない場合は一時ファイル）

    Returns:
        str: 保存したファイルパス or None
    """
    if not url:
        logger.error("画像URLが指定されていません")
        return None

    # 保存パスを生成
    if not save_path:
        timestamp = int(time.time())
        ext = Path(url).suffix.lower() or ".jpg"
        if ext not in SUPPORTED_FORMATS:
            ext = ".jpg"
        save_path = str(TEMP_DIR / f"image_{timestamp}{ext}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()

            # ファイルサイズチェック
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > MAX_IMAGE_SIZE:
                logger.error(f"画像サイズが大きすぎます: {content_length} bytes")
                return None

            # ファイルを保存
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"画像をダウンロードしました: {save_path}")
            return save_path

        except requests.RequestException as e:
            logger.warning(f"ダウンロードエラー (試行 {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

    logger.error(f"画像のダウンロードに失敗しました: {url}")
    return None


def validate_image(file_path: str) -> bool:
    """
    画像ファイルを検証

    Args:
        file_path: 画像ファイルパス

    Returns:
        bool: 有効な画像かどうか
    """
    try:
        path = Path(file_path)

        # ファイル存在チェック
        if not path.exists():
            logger.error(f"ファイルが存在しません: {file_path}")
            return False

        # 拡張子チェック
        if path.suffix.lower() not in SUPPORTED_FORMATS:
            logger.error(f"サポートされていない画像形式です: {path.suffix}")
            return False

        # ファイルサイズチェック
        if path.stat().st_size > MAX_IMAGE_SIZE:
            logger.error(f"画像サイズが大きすぎます: {path.stat().st_size} bytes")
            return False

        # 画像として開けるかチェック
        with Image.open(file_path) as img:
            img.verify()

        return True

    except Exception as e:
        logger.error(f"画像検証エラー: {e}")
        return False


def optimize_image(file_path: str, max_width: int = 1920, quality: int = 85) -> str:
    """
    画像を最適化（リサイズ・圧縮）

    Args:
        file_path: 画像ファイルパス
        max_width: 最大幅
        quality: JPEG品質 (1-100)

    Returns:
        str: 最適化後のファイルパス
    """
    try:
        with Image.open(file_path) as img:
            # WebPをJPEGに変換
            if img.format == "WEBP":
                img = img.convert("RGB")

            # リサイズ
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # 保存
            output_path = str(Path(file_path).with_suffix(".jpg"))
            img.convert("RGB").save(output_path, "JPEG", quality=quality, optimize=True)

            logger.info(f"画像を最適化しました: {output_path}")
            return output_path

    except Exception as e:
        logger.error(f"画像最適化エラー: {e}")
        return file_path


def upload_to_imgbb(file_path: str) -> Optional[str]:
    """
    画像をimgBBにアップロードして公開URLを返す

    Args:
        file_path: 画像ファイルパス

    Returns:
        str: 公開URL or None
    """
    if not IMGBB_API_KEY:
        logger.error("IMGBB_API_KEYが設定されていません")
        return None

    if not validate_image(file_path):
        return None

    try:
        # 画像をBase64エンコード
        with open(file_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # APIリクエスト
        response = requests.post(
            IMGBB_API_URL,
            params={"key": IMGBB_API_KEY},
            data={"image": image_data},
            timeout=60
        )
        response.raise_for_status()

        result = response.json()

        if result.get("success"):
            url = result["data"]["url"]
            logger.info(f"imgBBにアップロードしました: {url}")
            return url
        else:
            logger.error(f"imgBBアップロード失敗: {result}")
            return None

    except requests.RequestException as e:
        logger.error(f"imgBB APIエラー: {e}")
        return None
    except Exception as e:
        logger.error(f"アップロードエラー: {e}")
        return None


def get_hosted_url(image_url: str) -> Optional[str]:
    """
    画像URLをダウンロード→imgBBにアップロード→公開URLを返す

    Args:
        image_url: 元の画像URL

    Returns:
        str: imgBBの公開URL or None
    """
    # ダウンロード
    local_path = download_image(image_url)
    if not local_path:
        return None

    try:
        # 最適化（オプション）
        optimized_path = optimize_image(local_path)

        # アップロード
        hosted_url = upload_to_imgbb(optimized_path)

        return hosted_url

    finally:
        # 一時ファイルを削除
        cleanup_file(local_path)
        if local_path != optimized_path:
            cleanup_file(optimized_path)


def cleanup_file(file_path: str) -> None:
    """一時ファイルを削除"""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"一時ファイルを削除しました: {file_path}")
    except Exception as e:
        logger.warning(f"ファイル削除エラー: {e}")


def cleanup_temp_images() -> int:
    """
    一時画像フォルダをクリーンアップ

    Returns:
        int: 削除したファイル数
    """
    count = 0
    try:
        for file in TEMP_DIR.iterdir():
            if file.is_file():
                file.unlink()
                count += 1

        if count > 0:
            logger.info(f"{count}件の一時ファイルを削除しました")

    except Exception as e:
        logger.error(f"クリーンアップエラー: {e}")

    return count


if __name__ == "__main__":
    from config import setup_logging
    setup_logging()

    # テスト用画像URL
    test_url = "https://via.placeholder.com/500x500.jpg"

    print("画像ホスティングテスト")
    print("=" * 50)

    # ダウンロードテスト
    local_path = download_image(test_url)
    if local_path:
        print(f"ダウンロード成功: {local_path}")

        # 検証テスト
        if validate_image(local_path):
            print("画像検証: OK")

        # imgBBテスト（APIキーが設定されている場合）
        if IMGBB_API_KEY:
            hosted_url = upload_to_imgbb(local_path)
            if hosted_url:
                print(f"imgBBアップロード成功: {hosted_url}")
        else:
            print("IMGBB_API_KEYが未設定のためスキップ")

        # クリーンアップ
        cleanup_file(local_path)
    else:
        print("ダウンロード失敗")
