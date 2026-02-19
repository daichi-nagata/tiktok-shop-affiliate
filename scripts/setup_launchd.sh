#!/bin/bash
# launchdセットアップスクリプト
# TikTok Shop アフィリエイト自動投稿の定期実行を設定

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

echo "TikTok Shop アフィリエイト - launchd セットアップ"
echo "================================================"

# LaunchAgentsディレクトリ作成
mkdir -p "$LAUNCH_AGENTS_DIR"

# plistファイルをコピー
echo "plistファイルをコピー中..."
cp "$SCRIPT_DIR/com.tiktok-affiliate.post.plist" "$LAUNCH_AGENTS_DIR/"
cp "$SCRIPT_DIR/com.tiktok-affiliate.research.plist" "$LAUNCH_AGENTS_DIR/"

# 既存のジョブをアンロード（エラーは無視）
echo "既存ジョブをアンロード中..."
launchctl unload "$LAUNCH_AGENTS_DIR/com.tiktok-affiliate.post.plist" 2>/dev/null
launchctl unload "$LAUNCH_AGENTS_DIR/com.tiktok-affiliate.research.plist" 2>/dev/null

# 新しいジョブをロード
echo "新しいジョブをロード中..."
launchctl load "$LAUNCH_AGENTS_DIR/com.tiktok-affiliate.post.plist"
launchctl load "$LAUNCH_AGENTS_DIR/com.tiktok-affiliate.research.plist"

# 状態確認
echo ""
echo "設定完了！ジョブ状態:"
launchctl list | grep tiktok-affiliate

echo ""
echo "スケジュール:"
echo "  - 投稿: 毎日 8:00, 14:00, 20:00"
echo "  - リサーチ: 毎週月曜 7:00"
echo ""
echo "手動実行:"
echo "  launchctl start com.tiktok-affiliate.post"
echo "  launchctl start com.tiktok-affiliate.research"
echo ""
echo "停止:"
echo "  launchctl unload ~/Library/LaunchAgents/com.tiktok-affiliate.post.plist"
echo "  launchctl unload ~/Library/LaunchAgents/com.tiktok-affiliate.research.plist"
