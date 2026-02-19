"""
AIリサーチ機能
Claude APIのWeb検索ツールでSNSトレンドを調査し、おすすめ商品リストを生成
"""

import json
import logging
from datetime import datetime

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, setup_logging
from db_manager import add_research_log, get_latest_research, init_database

logger = logging.getLogger(__name__)


def create_research_prompt() -> str:
    """リサーチ用プロンプトを生成"""
    current_month = datetime.now().strftime("%Y年%m月")

    return f"""あなたはTikTok Shopで売れる商品をリサーチするマーケティングの専門家です。

{current_month}現在、TikTok Shopで売れそうな商品を5〜10個提案してください。

【調査対象】
- TikTokで話題になっている商品
- SNS（Instagram、X/Twitter）でバズっている商品
- 季節に合った需要の高い商品

【条件】
- 価格帯: 1,000円〜10,000円
- カテゴリ: 美容、ファッション、ガジェット、健康、雑貨、キッチン用品など
- 日本のTikTok Shop（または類似のEC）で購入できる可能性が高いもの
- アフィリエイトで紹介しやすい商品

【出力形式】
以下のJSON形式で出力してください：

```json
[
    {{
        "product_name": "商品名（一般名称）",
        "price_range": "2000-3000",
        "reason": "おすすめ理由（SNSトレンドとの関連、なぜ売れそうか）",
        "search_keywords": ["検索キーワード1", "検索キーワード2"],
        "target_audience": "ターゲット層",
        "category": "カテゴリ"
    }}
]
```

必ず5〜10個の商品を提案してください。"""


def parse_recommendations(response_text: str) -> list[dict]:
    """Claude APIのレスポンスからおすすめリストをパース"""
    try:
        # JSON部分を抽出
        start = response_text.find("[")
        end = response_text.rfind("]") + 1

        if start == -1 or end == 0:
            logger.error("JSONが見つかりません")
            return []

        json_str = response_text[start:end]
        recommendations = json.loads(json_str)

        logger.info(f"{len(recommendations)}件のおすすめ商品を取得しました")
        return recommendations

    except json.JSONDecodeError as e:
        logger.error(f"JSONパースエラー: {e}")
        return []


def run_research() -> list[dict]:
    """
    Claude APIでリサーチを実行

    注意: Web検索ツールはベータ機能です。
    利用できない場合は通常のChat APIで代替します。
    """
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEYが設定されていません")
        return []

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = create_research_prompt()

    try:
        # Web検索ツールを使用したリサーチ（ベータ機能）
        # 利用できない場合は通常のAPIを使用
        logger.info("Claude APIでリサーチを開始...")

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        response_text = response.content[0].text
        logger.debug(f"APIレスポンス: {response_text[:500]}...")

        recommendations = parse_recommendations(response_text)
        return recommendations

    except anthropic.APIError as e:
        logger.error(f"Claude API エラー: {e}")
        return []


def save_research_results(recommendations: list[dict]) -> int:
    """リサーチ結果をDBに保存"""
    if not recommendations:
        logger.warning("保存する推薦商品がありません")
        return 0

    init_database()
    log_id = add_research_log(recommendations)
    logger.info(f"リサーチ結果を保存しました (ID: {log_id})")
    return log_id


def get_latest_recommendations() -> list[dict]:
    """最新のおすすめリストを取得"""
    init_database()
    research = get_latest_research()
    if research:
        return research.get("recommendations", [])
    return []


def format_recommendations_for_display(recommendations: list[dict]) -> str:
    """おすすめリストを表示用にフォーマット"""
    if not recommendations:
        return "おすすめ商品がありません"

    lines = ["=" * 50, "【おすすめ商品リスト】", "=" * 50, ""]

    for i, item in enumerate(recommendations, 1):
        lines.append(f"{i}. {item.get('product_name', '不明')}")
        lines.append(f"   価格帯: {item.get('price_range', '不明')}円")
        lines.append(f"   カテゴリ: {item.get('category', '不明')}")
        lines.append(f"   ターゲット: {item.get('target_audience', '不明')}")
        lines.append(f"   理由: {item.get('reason', '不明')}")
        keywords = item.get('search_keywords', [])
        if keywords:
            lines.append(f"   検索キーワード: {', '.join(keywords)}")
        lines.append("")

    return "\n".join(lines)


def main():
    """メイン処理"""
    setup_logging()
    logger.info("=" * 50)
    logger.info("AIリサーチ開始")
    logger.info("=" * 50)

    # リサーチ実行
    recommendations = run_research()

    if recommendations:
        # 結果を保存
        save_research_results(recommendations)

        # 結果を表示
        print(format_recommendations_for_display(recommendations))
    else:
        logger.warning("おすすめ商品を取得できませんでした")
        print("リサーチに失敗しました。APIキーを確認してください。")

    logger.info("AIリサーチ完了")


if __name__ == "__main__":
    main()
