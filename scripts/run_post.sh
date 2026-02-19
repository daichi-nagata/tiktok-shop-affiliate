#!/bin/bash
# TikTok Shop アフィリエイト投稿スクリプト
# cronやlaunchdから実行される

# プロジェクトディレクトリ
PROJECT_DIR="/Users/daichi/Desktop/dev/claude-code/tiktok-shop-affiliate"

# ログファイル
LOG_FILE="${PROJECT_DIR}/logs/cron.log"

# 仮想環境のPython
PYTHON="${PROJECT_DIR}/venv/bin/python"

# ログに日時を記録
echo "========================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 投稿処理開始" >> "$LOG_FILE"

# 投稿を実行
cd "$PROJECT_DIR" && "$PYTHON" main.py >> "$LOG_FILE" 2>&1

# 終了コードをログに記録
EXIT_CODE=$?
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 終了コード: $EXIT_CODE" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

exit $EXIT_CODE
