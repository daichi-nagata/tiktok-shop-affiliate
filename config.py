"""
設定・環境変数管理
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートディレクトリ
BASE_DIR = Path(__file__).parent

# .envファイルを読み込み
load_dotenv(BASE_DIR / ".env")


# =============================================================================
# API Keys
# =============================================================================

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "")


# =============================================================================
# Paths
# =============================================================================

DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = BASE_DIR / "images"
LOGS_DIR = BASE_DIR / "logs"

DATABASE_PATH = DATA_DIR / "posts.db"
URLS_FILE_PATH = DATA_DIR / "urls.txt"
TOKENS_FILE_PATH = DATA_DIR / "tiktok_tokens.json"


# =============================================================================
# Claude API Settings
# =============================================================================

CLAUDE_MODEL = "claude-sonnet-4-5-20250929"


# =============================================================================
# TikTok API Settings
# =============================================================================

TIKTOK_API_BASE_URL = "https://open.tiktokapis.com"
TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"


# =============================================================================
# imgBB Settings
# =============================================================================

IMGBB_API_URL = "https://api.imgbb.com/1/upload"


# =============================================================================
# Logging
# =============================================================================

def setup_logging():
    """ログ設定を初期化"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR / "cron.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )


# =============================================================================
# Validation
# =============================================================================

def validate_config():
    """設定値を検証"""
    errors = []

    if not ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY が設定されていません")

    if not TIKTOK_CLIENT_KEY:
        errors.append("TIKTOK_CLIENT_KEY が設定されていません")

    if not TIKTOK_CLIENT_SECRET:
        errors.append("TIKTOK_CLIENT_SECRET が設定されていません")

    if not IMGBB_API_KEY:
        errors.append("IMGBB_API_KEY が設定されていません")

    if errors:
        raise ValueError("設定エラー:\n" + "\n".join(errors))


# ディレクトリを作成
DATA_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
