# 01. 環境構築・初期設定

## 概要
プロジェクトの環境構築と初期設定を行う。

## タスク一覧

### 環境構築
- [x] Python仮想環境を作成 (`python -m venv venv`)
- [x] 仮想環境を有効化
- [x] requirements.txtを作成
- [x] 必要パッケージをインストール

### 必要パッケージ
```
requests
beautifulsoup4
anthropic
python-dotenv
Pillow
```

### ディレクトリ構成
- [x] data/ フォルダ作成
- [x] images/ フォルダ作成
- [x] logs/ フォルダ作成

### 設定ファイル
- [x] .env.example ファイルを作成
- [x] config.py を作成（環境変数読み込み）
- [x] .gitignore を作成

### .env.example の内容
```
ANTHROPIC_API_KEY=your_claude_api_key
TIKTOK_CLIENT_KEY=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret
TIKTOK_ACCESS_TOKEN=your_tiktok_access_token
IMGBB_API_KEY=your_imgbb_api_key
```

### config.py の実装内容
- [x] dotenvで.envファイルを読み込み
- [x] 各APIキーを定数として定義
- [x] 設定値の検証機能

## 完了条件
- [x] `python -c "import config"` がエラーなく実行できる
- [x] 全ディレクトリが存在する
- [x] .envファイルが正しく読み込める

## 関連ファイル
- `config.py`
- `.env`
- `.env.example`
- `requirements.txt`
- `.gitignore`

## 備考
- APIキーは絶対にGitにコミットしない
- .envは.gitignoreに含める
