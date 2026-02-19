# 04. AIリサーチ機能

## 概要
Claude APIのWeb検索ツールを使用してSNSトレンドを調査し、おすすめ商品リストを生成する。

## タスク一覧

### Claude API連携
- [x] Anthropic SDKのセットアップ
- [x] Web検索ツールの設定
- [x] API呼び出し処理の実装

### リサーチロジック
- [x] トレンド調査プロンプトの作成
- [x] 結果のパース処理
- [x] DBへの保存

### 出力フォーマット
- [x] おすすめ商品リストの構造定義
- [x] JSON形式での保存

## researcher.py の実装

### 使用モデル
- `claude-sonnet-4-5-20250929`

### プロンプト設計
```
あなたはTikTok Shopで売れる商品をリサーチするマーケティングの専門家です。

以下の条件で、今TikTok Shopで売れそうな商品を5〜10個提案してください。

【条件】
- TikTokで話題になっている商品
- 価格帯: 1,000円〜5,000円
- カテゴリ: 美容、ファッション、ガジェット、健康、雑貨
- 季節性を考慮
- SNSでバズりやすい要素がある

【出力形式】
各商品について以下の情報を出力してください：
1. 商品名（一般名称）
2. 推定価格帯
3. おすすめ理由（SNSトレンドとの関連）
4. TikTok Shopでの検索キーワード
5. ターゲット層
```

### 関数一覧
- [x] `create_research_prompt()` - リサーチ用プロンプト生成
- [x] `run_research()` - Claude APIでリサーチ実行
- [x] `parse_recommendations(response)` - 結果パース
- [x] `save_research_results(data)` - DB保存
- [x] `get_latest_recommendations()` - 最新おすすめ取得

### 出力形式（JSON）
```json
{
    "research_date": "2025-01-15",
    "recommendations": [
        {
            "product_name": "ポータブルネックファン",
            "price_range": "2000-3000",
            "reason": "夏に向けて需要増。TikTokで#熱中症対策 が急上昇中",
            "search_keywords": ["ネックファン", "首かけ扇風機", "ハンズフリー扇風機"],
            "target_audience": "20-30代女性、通勤・外出が多い人"
        }
    ]
}
```

## 実行スケジュール
- 毎週月曜 7:00 に自動実行
- 結果はresearch_logsテーブルに保存

## 完了条件
- [x] Claude APIでWeb検索が実行できる
- [x] おすすめリストがJSON形式で取得できる
- [x] 結果がDBに保存される
- [x] 最新のおすすめリストを取得できる

## 関連ファイル
- `researcher.py`
- `db_manager.py`（research_logsテーブル）

## 備考
- Claude APIのWeb検索機能はベータ版の可能性あり
- 検索結果の品質は変動する可能性がある
- プロンプトは定期的に改善する
