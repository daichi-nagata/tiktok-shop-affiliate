#!/usr/bin/env python3
"""
TikTok Shop アフィリエイト自動投稿システム
メイン実行スクリプト
"""

import argparse
import logging
import sys
from datetime import datetime

from config import setup_logging
from db_manager import init_database, add_post_log, update_product
from product_manager import get_next_product_for_posting
from image_host import get_hosted_url, cleanup_temp_images
from ai_writer import generate_post_text
from tiktok_poster import post_product

logger = logging.getLogger(__name__)


def run_single_post(dry_run: bool = False, product_id: str = None) -> bool:
    """
    1回の投稿処理を実行

    Args:
        dry_run: ドライラン（実際に投稿しない）
        product_id: 指定商品ID（省略時はローテーション）

    Returns:
        bool: 成功したかどうか
    """
    try:
        # 1. 投稿対象商品を選択
        if product_id:
            from db_manager import get_product
            product = get_product(product_id)
            if not product:
                logger.error(f"商品が見つかりません: {product_id}")
                return False
        else:
            product = get_next_product_for_posting()

        if not product:
            logger.warning("投稿対象の商品がありません")
            return False

        logger.info(f"商品選択: {product['item_name']} (ID: {product['item_id']})")

        # 2. 画像をホスティング
        if not product.get("image_url"):
            logger.error("商品の画像URLがありません")
            return False

        logger.info("画像をホスティング中...")
        hosted_image_url = get_hosted_url(product["image_url"])

        if not hosted_image_url:
            logger.error("画像のホスティングに失敗しました")
            return False

        logger.info(f"画像ホスティング完了: {hosted_image_url}")

        # 3. 投稿文を生成
        logger.info("投稿文を生成中...")
        post_data = generate_post_text(product)

        if not post_data:
            logger.error("投稿文の生成に失敗しました")
            return False

        logger.info(f"投稿文生成完了: {len(post_data['body'])}文字, {len(post_data['hashtags'])}個のハッシュタグ")

        # ドライランの場合はここで終了
        if dry_run:
            logger.info("=== ドライラン結果 ===")
            logger.info(f"商品: {product['item_name']}")
            logger.info(f"画像URL: {hosted_image_url}")
            logger.info(f"投稿文:\n{post_data['full_text']}")
            return True

        # 4. TikTokに投稿
        logger.info("TikTokに投稿中...")
        result = post_product(
            product=product,
            post_text=post_data["full_text"],
            image_url=hosted_image_url
        )

        if not result:
            logger.error("TikTok投稿に失敗しました")
            return False

        if result.get("success"):
            logger.info(f"TikTok投稿完了: publish_id={result['publish_id']}")

            # 5. 結果を記録
            add_post_log({
                "item_id": product["item_id"],
                "post_text": post_data["full_text"],
                "hosted_image_url": hosted_image_url,
                "tiktok_publish_id": result["publish_id"],
                "status": "published"
            })

            update_product(product["item_id"], {
                "last_posted_at": datetime.now().isoformat(),
                "post_count": product.get("post_count", 0) + 1
            })

            logger.info("投稿ログを記録しました")
            return True
        else:
            logger.error(f"投稿失敗: {result.get('fail_reason', 'Unknown')}")

            # 失敗ログを記録
            add_post_log({
                "item_id": product["item_id"],
                "post_text": post_data["full_text"],
                "hosted_image_url": hosted_image_url,
                "tiktok_publish_id": result.get("publish_id"),
                "status": "failed"
            })
            return False

    except Exception as e:
        logger.error(f"投稿処理エラー: {e}", exc_info=True)
        return False


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="TikTok Shop アフィリエイト自動投稿システム"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ドライラン（実際に投稿しない）"
    )
    parser.add_argument(
        "--product-id",
        type=str,
        help="投稿する商品ID（省略時はローテーション）"
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="データベースを初期化"
    )

    args = parser.parse_args()

    # ログ設定
    setup_logging()

    logger.info("=" * 50)
    logger.info(f"投稿処理開始: {datetime.now()}")
    logger.info("=" * 50)

    # データベース初期化
    init_database()

    if args.init_db:
        logger.info("データベースを初期化しました")
        return

    try:
        # 投稿処理を実行
        success = run_single_post(
            dry_run=args.dry_run,
            product_id=args.product_id
        )

        if success:
            logger.info("=== 投稿処理完了 ===")
        else:
            logger.warning("=== 投稿処理失敗 ===")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("処理を中断しました")
        sys.exit(1)

    except Exception as e:
        logger.error(f"予期せぬエラー: {e}", exc_info=True)
        sys.exit(1)

    finally:
        # クリーンアップ
        cleanup_temp_images()


if __name__ == "__main__":
    main()
