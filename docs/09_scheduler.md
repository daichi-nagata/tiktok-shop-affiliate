# 09. 自動実行設定

## 概要
cron/launchdを使用して、AIリサーチと投稿処理を自動実行する設定を行う。

## タスク一覧

### cron設定
- [x] AIリサーチのcron設定（週1回）
- [x] 投稿処理のcron設定（1日3回）
- [x] ログローテーション設定

### launchd設定（Mac推奨）
- [x] plistファイルの作成
- [x] launchdへの登録
- [x] スリープ復帰後の実行確認

### 動作確認
- [x] 手動実行テスト
- [x] 自動実行テスト
- [x] ログ出力確認

## スケジュール

| 処理 | 頻度 | 時刻 |
|------|------|------|
| AIリサーチ (researcher.py) | 週1回 | 月曜 7:00 |
| 投稿 (main.py) | 1日3回 | 8:00, 14:00, 20:00 |

## launchdセットアップ（推奨）

### 簡単セットアップ
```bash
cd /Users/daichi/Desktop/dev/claude-code/tiktok-shop-affiliate
./scripts/setup_launchd.sh
```

### 手動セットアップ
```bash
# plistファイルをコピー
cp scripts/com.tiktok-affiliate.post.plist ~/Library/LaunchAgents/
cp scripts/com.tiktok-affiliate.research.plist ~/Library/LaunchAgents/

# launchdに読み込み
launchctl load ~/Library/LaunchAgents/com.tiktok-affiliate.post.plist
launchctl load ~/Library/LaunchAgents/com.tiktok-affiliate.research.plist

# 状態確認
launchctl list | grep tiktok-affiliate
```

### 管理コマンド
```bash
# 手動実行（テスト用）
launchctl start com.tiktok-affiliate.post
launchctl start com.tiktok-affiliate.research

# 停止
launchctl unload ~/Library/LaunchAgents/com.tiktok-affiliate.post.plist
launchctl unload ~/Library/LaunchAgents/com.tiktok-affiliate.research.plist
```

## cron設定（代替）

```bash
# crontabを編集
crontab -e

# 以下を追加
# AIリサーチ（毎週月曜 7:00）
0 7 * * 1 cd /Users/daichi/Desktop/dev/claude-code/tiktok-shop-affiliate && ./venv/bin/python researcher.py >> logs/cron.log 2>&1

# 投稿（1日3回: 8:00, 14:00, 20:00）
0 8 * * * cd /Users/daichi/Desktop/dev/claude-code/tiktok-shop-affiliate && ./venv/bin/python main.py >> logs/cron.log 2>&1
0 14 * * * cd /Users/daichi/Desktop/dev/claude-code/tiktok-shop-affiliate && ./venv/bin/python main.py >> logs/cron.log 2>&1
0 20 * * * cd /Users/daichi/Desktop/dev/claude-code/tiktok-shop-affiliate && ./venv/bin/python main.py >> logs/cron.log 2>&1
```

## 作成されたファイル

```
scripts/
├── run_post.sh                      # 投稿用シェルスクリプト
├── run_research.sh                  # リサーチ用シェルスクリプト
├── setup_launchd.sh                 # launchdセットアップスクリプト
├── com.tiktok-affiliate.post.plist  # 投稿用plist
└── com.tiktok-affiliate.research.plist  # リサーチ用plist
```

## 完了条件
- [x] cron または launchd で自動実行が動作する
- [x] 指定時刻に処理が実行される
- [x] ログファイルに実行結果が記録される
- [x] エラー発生時もログに記録される

## 関連ファイル
- `scripts/setup_launchd.sh`
- `scripts/com.tiktok-affiliate.*.plist`
- `logs/cron.log`
- `logs/launchd.log`

## 備考
- Macでは基本的にlaunchdを推奨（スリープ対応）
- サーバー環境ではcronを使用
- ログは定期的に確認し、エラーを監視
