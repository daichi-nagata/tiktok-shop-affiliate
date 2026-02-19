"""
投稿文生成機能
Claude APIで商品紹介文とハッシュタグを自動生成
"""

import logging
import re
from typing import Optional

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

logger = logging.getLogger(__name__)

# 文体バリエーション
STYLE_TEMPLATES = {
    "enthusiastic": "熱狂的でテンション高めに、商品の魅力を強調して",
    "casual": "友達に話しかけるようにカジュアルで親しみやすく",
    "informative": "商品の特徴や使い方を分かりやすく説明するように",
    "story": "実際に使った体験談風に、ビフォーアフターを交えて",
}


def create_post_prompt(product: dict, style: str = "casual") -> str:
    """投稿文生成用プロンプトを作成"""
    style_instruction = STYLE_TEMPLATES.get(style, STYLE_TEMPLATES["casual"])

    return f"""あなたはTikTokで商品を紹介する人気クリエイターです。
以下の商品について、TikTokフォト投稿用の紹介文を書いてください。

【商品情報】
商品名: {product.get('item_name', '不明')}
価格: {product.get('price', '不明')}円
カテゴリ: {product.get('category', '不明')}
説明: {product.get('description', '商品の説明文がありません')}

【ルール】
- 300文字以内（必須）
- 絵文字を適度に使用（3〜5個）
- 冒頭に「PR」を入れる（ステマ規制対応）
- 商品の魅力・使用シーンを具体的に
- 呼びかけ調で親しみやすく
- 「TikTok Shopでチェック」など購買を促す一文を入れる
- {style_instruction}

【出力形式】
本文:
（紹介文をここに。「PR」から始めること）

ハッシュタグ:
#タグ1 #タグ2 #タグ3 #タグ4 #タグ5 #タグ6 #タグ7

必ず上記の形式で出力してください。"""


def parse_response(response_text: str) -> dict:
    """
    APIレスポンスから本文とハッシュタグを抽出

    Returns:
        dict: {"body": str, "hashtags": list, "full_text": str}
    """
    result = {
        "body": "",
        "hashtags": [],
        "full_text": ""
    }

    # 本文を抽出
    body_match = re.search(r"本文[:：]?\s*\n(.+?)(?=\nハッシュタグ|\n#|$)", response_text, re.DOTALL)
    if body_match:
        result["body"] = body_match.group(1).strip()
    else:
        # フォールバック: PRで始まる部分を探す
        pr_match = re.search(r"(PR.+?)(?=\n#|\n\nハッシュタグ|$)", response_text, re.DOTALL)
        if pr_match:
            result["body"] = pr_match.group(1).strip()

    # ハッシュタグを抽出
    hashtags = re.findall(r"#[\w\u3040-\u30FF\u4E00-\u9FFF]+", response_text)
    result["hashtags"] = hashtags[:7]  # 最大7個

    # フルテキストを作成
    if result["body"]:
        hashtag_str = " ".join(result["hashtags"])
        result["full_text"] = f"{result['body']}\n\n{hashtag_str}"

    return result


def validate_post_text(text: str) -> dict:
    """
    投稿文を検証

    Returns:
        dict: {"valid": bool, "errors": list}
    """
    errors = []

    # 文字数チェック（ハッシュタグを除く本文）
    body = re.sub(r"#[\w\u3040-\u30FF\u4E00-\u9FFF]+", "", text).strip()
    if len(body) > 300:
        errors.append(f"本文が300文字を超えています（{len(body)}文字）")

    # PR表記チェック
    if not text.startswith("PR"):
        errors.append("冒頭にPR表記がありません")

    # ハッシュタグ数チェック
    hashtags = re.findall(r"#[\w\u3040-\u30FF\u4E00-\u9FFF]+", text)
    if len(hashtags) < 5:
        errors.append(f"ハッシュタグが5個未満です（{len(hashtags)}個）")
    elif len(hashtags) > 7:
        errors.append(f"ハッシュタグが7個を超えています（{len(hashtags)}個）")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def generate_post_text(product: dict, style: str = "casual", max_retries: int = 2) -> Optional[dict]:
    """
    商品情報から投稿文を生成

    Args:
        product: 商品情報の辞書
        style: 文体スタイル
        max_retries: リトライ回数

    Returns:
        dict: {"body": str, "hashtags": list, "full_text": str} or None
    """
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEYが設定されていません")
        return None

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = create_post_prompt(product, style)

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"投稿文生成中... (試行 {attempt + 1})")

            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            response_text = response.content[0].text
            logger.debug(f"APIレスポンス: {response_text}")

            # レスポンスをパース
            result = parse_response(response_text)

            if not result["body"]:
                logger.warning("本文を抽出できませんでした")
                continue

            # 検証
            validation = validate_post_text(result["full_text"])
            if validation["valid"]:
                logger.info(f"投稿文生成成功: {len(result['body'])}文字, {len(result['hashtags'])}個のハッシュタグ")
                return result
            else:
                logger.warning(f"検証エラー: {validation['errors']}")

        except anthropic.APIError as e:
            logger.error(f"Claude API エラー: {e}")

    logger.error("投稿文の生成に失敗しました")
    return None


def generate_multiple_variations(product: dict, count: int = 3) -> list[dict]:
    """
    複数の文体で投稿文を生成

    Args:
        product: 商品情報
        count: 生成する数

    Returns:
        list: 投稿文のリスト
    """
    styles = list(STYLE_TEMPLATES.keys())[:count]
    results = []

    for style in styles:
        result = generate_post_text(product, style)
        if result:
            result["style"] = style
            results.append(result)

    return results


if __name__ == "__main__":
    from config import setup_logging
    setup_logging()

    # テスト用商品データ
    test_product = {
        "item_name": "ポータブルネックファン",
        "price": 2980,
        "category": "ガジェット",
        "description": "首にかけるだけで涼しい風が楽しめるハンズフリー扇風機。USB充電式で最大8時間使用可能。静音設計で通勤にもぴったり。"
    }

    print("投稿文生成テスト")
    print("=" * 50)

    result = generate_post_text(test_product)
    if result:
        print(f"\n【生成された投稿文】\n{result['full_text']}")
        print(f"\n【文字数】本文: {len(result['body'])}文字")
        print(f"【ハッシュタグ数】{len(result['hashtags'])}個")
    else:
        print("投稿文の生成に失敗しました")
