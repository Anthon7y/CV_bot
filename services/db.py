import sqlite3
import logging
from datetime import date
from contextlib import contextmanager
from config import DB_FILE

logger = logging.getLogger(__name__)


def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_cursor():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Создаёт таблицы если не существуют."""
    with db_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                subscribed INTEGER DEFAULT 1,
                last_prediction_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS rune_stats (
                rune_name TEXT PRIMARY KEY,
                request_count INTEGER DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_text TEXT,
                message_photo TEXT,
                message_document TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    logger.info("База данных инициализирована.")


def upsert_user(user_id: int, username: str, first_name: str, last_name: str):
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name
        """, (user_id, username, first_name, last_name))


def toggle_subscription(user_id: int, subscribe: bool):
    """Подписывает или отписывает пользователя."""
    with db_cursor() as cur:
        cur.execute(
            "UPDATE users SET subscribed = ? WHERE user_id = ?",
            (1 if subscribe else 0, user_id)
        )


def is_user_subscribed(user_id: int) -> bool:
    """Проверяет, подписан ли пользователь."""
    with db_cursor() as cur:
        cur.execute("SELECT subscribed FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return row and row["subscribed"] == 1


def get_user(user_id: int):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cur.fetchone()


def get_last_prediction_date(user_id: int) -> str | None:
    """Возвращает дату последнего предсказания в формате ISO (YYYY-MM-DD) или None."""
    with db_cursor() as cur:
        cur.execute("SELECT last_prediction_date FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row and row["last_prediction_date"]:
            return row["last_prediction_date"]
        return None


def set_last_prediction_date(user_id: int, prediction_date: date):
    with db_cursor() as cur:
        cur.execute(
            "UPDATE users SET last_prediction_date = ? WHERE user_id = ?",
            (prediction_date.isoformat(), user_id)
        )


def get_subscribed_users() -> list[int]:
    with db_cursor() as cur:
        cur.execute("SELECT user_id FROM users WHERE subscribed = 1")
        return [row["user_id"] for row in cur.fetchall()]


def get_all_users() -> list[int]:
    with db_cursor() as cur:
        cur.execute("SELECT user_id FROM users")
        return [row["user_id"] for row in cur.fetchall()]


def get_stats() -> dict:
    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) as total FROM users")
        total = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) as sub FROM users WHERE subscribed = 1")
        subscribed = cur.fetchone()["sub"]

        today = date.today().isoformat()
        cur.execute(
            "SELECT COUNT(*) as active FROM users WHERE last_prediction_date = ?",
            (today,)
        )
        active_today = cur.fetchone()["active"]

    return {
        "total": total,
        "subscribed": subscribed,
        "unsubscribed": total - subscribed,
        "active_today": active_today,
    }


def increment_rune_stat(rune_name: str):
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO rune_stats (rune_name, request_count)
            VALUES (?, 1)
            ON CONFLICT(rune_name) DO UPDATE SET
                request_count = request_count + 1
        """, (rune_name,))


# --- Broadcasts ---

def save_broadcast(message_text=None, message_photo=None, message_document=None):
    """Сохраняет рассылку в БД."""
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO broadcasts (message_text, message_photo, message_document)
            VALUES (?, ?, ?)
        """, (message_text, message_photo, message_document))
        return cur.lastrowid


def get_broadcasts(limit=10):
    """Возвращает последние рассылки."""
    with db_cursor() as cur:
        cur.execute("""
            SELECT id, message_text, message_photo, message_document, sent_at
            FROM broadcasts
            ORDER BY sent_at DESC
            LIMIT ?
        """, (limit,))
        return cur.fetchall()


def get_broadcast_by_id(broadcast_id: int):
    """Возвращает одну рассылку по ID."""
    with db_cursor() as cur:
        cur.execute("""
            SELECT id, message_text, message_photo, message_document, sent_at
            FROM broadcasts
            WHERE id = ?
        """, (broadcast_id,))
        return cur.fetchone()
