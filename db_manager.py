"""
SQLiteデータベース管理
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

from config import DATABASE_PATH


@contextmanager
def get_connection():
    """データベース接続のコンテキストマネージャー"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """データベースを初期化（テーブル作成）"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 商品テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT UNIQUE NOT NULL,
                item_name TEXT NOT NULL,
                price INTEGER,
                image_url TEXT,
                category TEXT,
                description TEXT,
                affiliate_url TEXT,
                last_posted_at DATETIME,
                post_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 投稿ログテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT NOT NULL,
                post_text TEXT,
                hosted_image_url TEXT,
                tiktok_publish_id TEXT,
                status TEXT DEFAULT 'pending',
                posted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES products(item_id)
            )
        """)

        # AIリサーチログテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                research_date DATE NOT NULL,
                recommendations TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)


# =============================================================================
# 商品管理
# =============================================================================

def add_product(product_data: dict) -> int:
    """商品を追加"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO products
            (item_id, item_name, price, image_url, category, description, affiliate_url, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product_data["item_id"],
            product_data["item_name"],
            product_data.get("price"),
            product_data.get("image_url"),
            product_data.get("category"),
            product_data.get("description"),
            product_data.get("affiliate_url"),
            datetime.now().isoformat()
        ))
        return cursor.lastrowid


def get_product(item_id: str) -> Optional[dict]:
    """商品を取得"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE item_id = ?", (item_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_products(active_only: bool = True) -> list[dict]:
    """全商品を取得"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if active_only:
            cursor.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY created_at DESC")
        else:
            cursor.execute("SELECT * FROM products ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]


def get_products_for_posting() -> list[dict]:
    """
    投稿対象商品を取得（ローテーション）
    優先順位:
    1. まだ一度も投稿していない商品
    2. 投稿回数が少ない商品
    3. 最終投稿から時間が経っている商品
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM products
            WHERE is_active = 1
            ORDER BY
                CASE WHEN last_posted_at IS NULL THEN 0 ELSE 1 END,
                post_count ASC,
                last_posted_at ASC
        """)
        return [dict(row) for row in cursor.fetchall()]


def update_product(item_id: str, data: dict) -> bool:
    """商品を更新"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 更新可能なフィールド
        allowed_fields = [
            "item_name", "price", "image_url", "category", "description",
            "affiliate_url", "last_posted_at", "post_count", "is_active"
        ]

        updates = []
        values = []
        for key, value in data.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                values.append(value)

        if not updates:
            return False

        updates.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(item_id)

        query = f"UPDATE products SET {', '.join(updates)} WHERE item_id = ?"
        cursor.execute(query, values)
        return cursor.rowcount > 0


def deactivate_product(item_id: str) -> bool:
    """商品を無効化"""
    return update_product(item_id, {"is_active": False})


# =============================================================================
# 投稿ログ
# =============================================================================

def add_post_log(post_data: dict) -> int:
    """投稿ログを追加"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO posts (item_id, post_text, hosted_image_url, tiktok_publish_id, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            post_data["item_id"],
            post_data.get("post_text"),
            post_data.get("hosted_image_url"),
            post_data.get("tiktok_publish_id"),
            post_data.get("status", "pending")
        ))
        return cursor.lastrowid


def get_recent_posts(limit: int = 10) -> list[dict]:
    """最近の投稿を取得"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM posts ORDER BY posted_at DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]


def update_post_status(post_id: int, status: str) -> bool:
    """投稿ステータスを更新"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE posts SET status = ? WHERE id = ?",
            (status, post_id)
        )
        return cursor.rowcount > 0


# =============================================================================
# リサーチログ
# =============================================================================

def add_research_log(recommendations: list[dict]) -> int:
    """リサーチログを追加"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO research_logs (research_date, recommendations)
            VALUES (?, ?)
        """, (
            datetime.now().date().isoformat(),
            json.dumps(recommendations, ensure_ascii=False)
        ))
        return cursor.lastrowid


def get_latest_research() -> Optional[dict]:
    """最新のリサーチログを取得"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM research_logs ORDER BY created_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result["recommendations"] = json.loads(result["recommendations"])
            return result
        return None


if __name__ == "__main__":
    # テスト実行
    init_database()
    print("データベース初期化完了")

    # テストデータ追加
    test_product = {
        "item_id": "test001",
        "item_name": "テスト商品",
        "price": 1980,
        "image_url": "https://example.com/image.jpg",
        "category": "テスト",
        "description": "テスト商品の説明",
        "affiliate_url": "https://example.com/product"
    }
    add_product(test_product)
    print("テスト商品追加完了")

    # 取得テスト
    product = get_product("test001")
    print(f"取得した商品: {product}")

    # 投稿対象取得
    products = get_products_for_posting()
    print(f"投稿対象商品数: {len(products)}")
