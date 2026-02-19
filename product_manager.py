"""
商品管理機能
URLリストから商品情報をスクレイピングしてDBに登録
"""

import re
import time
import logging
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from config import URLS_FILE_PATH
from db_manager import add_product, get_product, get_products_for_posting, init_database

logger = logging.getLogger(__name__)

# リクエストヘッダー
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ja,en;q=0.9",
}

# リトライ設定
MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒


def load_urls_from_file(filepath: str = None) -> list[str]:
    """URLファイルからURLリストを読み込み"""
    filepath = filepath or URLS_FILE_PATH

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        urls = []
        for line in lines:
            line = line.strip()
            # 空行とコメント行をスキップ
            if line and not line.startswith("#"):
                urls.append(line)

        logger.info(f"URLファイルから {len(urls)} 件のURLを読み込みました")
        return urls

    except FileNotFoundError:
        logger.warning(f"URLファイルが見つかりません: {filepath}")
        return []


def extract_item_id(url: str) -> Optional[str]:
    """URLから商品IDを抽出"""
    # TikTok Shop URL パターン
    # https://shop.tiktok.com/view/product/xxxxx
    # https://www.tiktok.com/view/product/xxxxx

    patterns = [
        r"/product/(\d+)",
        r"/view/product/(\d+)",
        r"product_id=(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    # URLからパスの最後の部分を取得
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    if path_parts:
        return path_parts[-1]

    return None


def scrape_product(url: str) -> Optional[dict]:
    """
    商品ページをスクレイピングして情報を取得

    注意: TikTok ShopのDOMは頻繁に変更される可能性があります。
    スクレイピングが失敗する場合は、手動CSV入力を使用してください。
    """
    item_id = extract_item_id(url)
    if not item_id:
        logger.error(f"商品IDを抽出できません: {url}")
        return None

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # 商品情報を抽出（セレクタはサイト構造に依存）
            product_data = {
                "item_id": item_id,
                "item_name": extract_product_name(soup) or f"商品_{item_id}",
                "price": extract_price(soup),
                "image_url": extract_image_url(soup),
                "category": extract_category(soup),
                "description": extract_description(soup),
                "affiliate_url": url,
            }

            logger.info(f"商品情報取得成功: {product_data['item_name']}")
            return product_data

        except requests.RequestException as e:
            logger.warning(f"リクエストエラー (試行 {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

    logger.error(f"商品情報の取得に失敗しました: {url}")
    return None


def extract_product_name(soup: BeautifulSoup) -> Optional[str]:
    """商品名を抽出"""
    # 複数のセレクタを試行
    selectors = [
        "h1",
        "[data-testid='product-title']",
        ".product-title",
        ".product-name",
        "meta[property='og:title']",
    ]

    for selector in selectors:
        if selector.startswith("meta"):
            element = soup.select_one(selector)
            if element and element.get("content"):
                return element["content"].strip()
        else:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)

    return None


def extract_price(soup: BeautifulSoup) -> Optional[int]:
    """価格を抽出"""
    selectors = [
        "[data-testid='product-price']",
        ".product-price",
        ".price",
        "meta[property='product:price:amount']",
    ]

    for selector in selectors:
        if selector.startswith("meta"):
            element = soup.select_one(selector)
            if element and element.get("content"):
                try:
                    return int(float(element["content"]))
                except ValueError:
                    continue
        else:
            element = soup.select_one(selector)
            if element:
                # 数字のみを抽出
                price_text = element.get_text(strip=True)
                numbers = re.findall(r"\d+", price_text.replace(",", ""))
                if numbers:
                    return int(numbers[0])

    return None


def extract_image_url(soup: BeautifulSoup) -> Optional[str]:
    """商品画像URLを抽出"""
    selectors = [
        "meta[property='og:image']",
        "[data-testid='product-image'] img",
        ".product-image img",
        ".gallery img",
    ]

    for selector in selectors:
        if selector.startswith("meta"):
            element = soup.select_one(selector)
            if element and element.get("content"):
                return element["content"]
        else:
            element = soup.select_one(selector)
            if element:
                return element.get("src") or element.get("data-src")

    return None


def extract_category(soup: BeautifulSoup) -> Optional[str]:
    """カテゴリを抽出"""
    selectors = [
        "[data-testid='breadcrumb']",
        ".breadcrumb",
        "meta[property='product:category']",
    ]

    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            if selector.startswith("meta"):
                return element.get("content")
            return element.get_text(strip=True)

    return None


def extract_description(soup: BeautifulSoup) -> Optional[str]:
    """商品説明を抽出"""
    selectors = [
        "meta[property='og:description']",
        "[data-testid='product-description']",
        ".product-description",
        ".description",
    ]

    for selector in selectors:
        if selector.startswith("meta"):
            element = soup.select_one(selector)
            if element and element.get("content"):
                return element["content"].strip()[:500]  # 最大500文字
        else:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)[:500]

    return None


def validate_product_data(data: dict) -> bool:
    """商品データの検証"""
    required_fields = ["item_id", "item_name"]
    for field in required_fields:
        if not data.get(field):
            logger.error(f"必須フィールドが不足: {field}")
            return False
    return True


def register_products_from_urls(filepath: str = None) -> dict:
    """
    URLファイルから商品を一括登録

    Returns:
        dict: 処理結果 {"success": int, "failed": int, "skipped": int}
    """
    init_database()
    urls = load_urls_from_file(filepath)

    result = {"success": 0, "failed": 0, "skipped": 0}

    for url in urls:
        item_id = extract_item_id(url)
        if not item_id:
            logger.warning(f"商品IDを抽出できません: {url}")
            result["failed"] += 1
            continue

        # 既存チェック
        existing = get_product(item_id)
        if existing:
            logger.info(f"既存の商品をスキップ: {item_id}")
            result["skipped"] += 1
            continue

        # スクレイピング
        product_data = scrape_product(url)
        if product_data and validate_product_data(product_data):
            add_product(product_data)
            result["success"] += 1
        else:
            result["failed"] += 1

        # レート制限対策
        time.sleep(1)

    logger.info(f"登録完了: 成功={result['success']}, 失敗={result['failed']}, スキップ={result['skipped']}")
    return result


def register_product_from_csv(csv_path: str) -> dict:
    """
    CSVファイルから商品を一括登録（フォールバック用）

    CSV形式:
    item_id,item_name,price,image_url,category,description,affiliate_url
    """
    import csv

    init_database()
    result = {"success": 0, "failed": 0}

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                product_data = {
                    "item_id": row.get("item_id"),
                    "item_name": row.get("item_name"),
                    "price": int(row["price"]) if row.get("price") else None,
                    "image_url": row.get("image_url"),
                    "category": row.get("category"),
                    "description": row.get("description"),
                    "affiliate_url": row.get("affiliate_url"),
                }

                if validate_product_data(product_data):
                    add_product(product_data)
                    result["success"] += 1
                else:
                    result["failed"] += 1

    except FileNotFoundError:
        logger.error(f"CSVファイルが見つかりません: {csv_path}")
    except Exception as e:
        logger.error(f"CSV読み込みエラー: {e}")

    return result


def get_next_product_for_posting() -> Optional[dict]:
    """投稿対象の商品を1つ取得"""
    products = get_products_for_posting()
    return products[0] if products else None


if __name__ == "__main__":
    from config import setup_logging
    setup_logging()

    # テスト: URLファイルから登録
    result = register_products_from_urls()
    print(f"処理結果: {result}")

    # 投稿対象商品を取得
    product = get_next_product_for_posting()
    if product:
        print(f"次の投稿対象: {product['item_name']}")
    else:
        print("投稿対象の商品がありません")
