"""成效追蹤模組：抓取 post/account insights，存入 SQLite。"""

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from threads_pipeline.threads_client import _request_with_retry

logger = logging.getLogger(__name__)

THREADS_API_BASE = "https://graph.threads.net/v1.0"

# ── Schema ──────────────────────────────────────────────
#
#  post_insights
#  ┌──────────────┬──────────┬──────────────┬───────┬───────┬─────────┬─────────┬────────┐
#  │ collected_at │ post_id  │ text_preview │ views │ likes │ replies │ reposts │ quotes │
#  │ (TEXT, UTC)  │ (TEXT)   │ (TEXT)       │ (INT) │ (INT) │ (INT)   │ (INT)   │ (INT)  │
#  └──────────────┴──────────┴──────────────┴───────┴───────┴─────────┴─────────┴────────┘
#  PK: (collected_at, post_id) — 同一天重跑 = upsert
#
#  account_insights
#  ┌──────────────┬───────────┬─────────────┬───────┬─────────┬─────────┐
#  │ collected_at │ followers │ total_views │ likes │ replies │ reposts │
#  │ (TEXT, UTC)  │ (INT)     │ (INT)       │ (INT) │ (INT)   │ (INT)   │
#  └──────────────┴───────────┴─────────────┴───────┴─────────┴─────────┘
#  PK: collected_at — 同一天重跑 = upsert

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS post_insights (
    collected_date      TEXT NOT NULL,
    post_id             TEXT NOT NULL,
    text_preview        TEXT,
    full_text           TEXT,
    posted_at           TEXT,
    post_hour_local     INTEGER,
    username            TEXT,
    views               INTEGER DEFAULT 0,
    likes               INTEGER DEFAULT 0,
    replies             INTEGER DEFAULT 0,
    reposts             INTEGER DEFAULT 0,
    quotes              INTEGER DEFAULT 0,
    author_reply_count  INTEGER DEFAULT 0,
    PRIMARY KEY (collected_date, post_id)
);

CREATE TABLE IF NOT EXISTS account_insights (
    collected_date TEXT NOT NULL PRIMARY KEY,
    followers      INTEGER DEFAULT 0,
    total_views    INTEGER DEFAULT 0,
    total_likes    INTEGER DEFAULT 0,
    total_replies  INTEGER DEFAULT 0,
    total_reposts  INTEGER DEFAULT 0
);
"""

UPSERT_POST_SQL = """
INSERT INTO post_insights (collected_date, post_id, text_preview, full_text, posted_at, post_hour_local, username, views, likes, replies, reposts, quotes, author_reply_count)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(collected_date, post_id) DO UPDATE SET
    full_text=excluded.full_text, post_hour_local=excluded.post_hour_local,
    views=excluded.views, likes=excluded.likes, replies=excluded.replies,
    reposts=excluded.reposts, quotes=excluded.quotes,
    author_reply_count=excluded.author_reply_count;
"""

UPSERT_ACCOUNT_SQL = """
INSERT INTO account_insights (collected_date, followers, total_views, total_likes, total_replies, total_reposts)
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT(collected_date) DO UPDATE SET
    followers=excluded.followers, total_views=excluded.total_views,
    total_likes=excluded.total_likes, total_replies=excluded.total_replies,
    total_reposts=excluded.total_reposts;
"""


def init_db(config: dict) -> sqlite3.Connection:
    """初始化 SQLite 資料庫，建表。"""
    insights_cfg = config.get("insights", {})
    data_dir = Path(insights_cfg.get("data_dir", "./data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / insights_cfg.get("db_name", "threads.db")

    conn = sqlite3.connect(str(db_path))
    conn.executescript(CREATE_TABLES_SQL)
    _migrate_schema(conn)
    return conn


def _migrate_schema(conn: sqlite3.Connection):
    """為已存在的 DB 新增缺少的欄位（向後相容）。"""
    cursor = conn.execute("PRAGMA table_info(post_insights)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    migrations = [
        ("full_text", "TEXT"),
        ("post_hour_local", "INTEGER"),
        ("author_reply_count", "INTEGER DEFAULT 0"),
    ]
    for col_name, col_type in migrations:
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE post_insights ADD COLUMN {col_name} {col_type}")
            logger.info("已新增欄位: %s", col_name)
    conn.commit()


def fetch_and_store_post_insights(config: dict, conn: sqlite3.Connection) -> int:
    """抓取所有貼文的 insights 並存入 SQLite。回傳抓取的貼文數。"""
    token = config["threads"]["access_token"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tz_name = config.get("insights", {}).get("timezone", "Asia/Taipei")

    # Step 1: 列出所有貼文
    posts = _fetch_all_posts(token)
    if not posts:
        print("  無貼文可抓取")
        return 0

    print(f"  取得 {len(posts)} 篇貼文，正在抓取 insights...")

    # 取得自己的 username
    username = posts[0].get("username", "") if posts else ""

    count = 0
    for p in posts:
        post_id = p["id"]
        try:
            insights = _fetch_single_post_insights(post_id, token)
            full_text = p.get("text", "")
            posted_at = p.get("timestamp", "")
            post_hour = _calc_post_hour_local(posted_at, tz_name)
            reply_count = _fetch_author_reply_count(post_id, username, token)

            conn.execute(UPSERT_POST_SQL, (
                today,
                post_id,
                full_text[:50].replace("\n", " "),
                full_text,
                posted_at,
                post_hour,
                p.get("username", ""),
                insights.get("views", 0),
                insights.get("likes", 0),
                insights.get("replies", 0),
                insights.get("reposts", 0),
                insights.get("quotes", 0),
                reply_count,
            ))
            count += 1
        except Exception as e:
            logger.warning("貼文 %s insights 抓取失敗: %s", post_id, e)

    conn.commit()
    return count


def fetch_and_store_account_insights(config: dict, conn: sqlite3.Connection) -> dict:
    """抓取帳號層級 insights 並存入 SQLite。回傳今日數據 dict。"""
    token = config["threads"]["access_token"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    data = _fetch_account_insights(token)
    if not data:
        return {}

    conn.execute(UPSERT_ACCOUNT_SQL, (
        today,
        data.get("followers", 0),
        data.get("total_views", 0),
        data.get("total_likes", 0),
        data.get("total_replies", 0),
        data.get("total_reposts", 0),
    ))
    conn.commit()
    return data


def get_trend(conn: sqlite3.Connection, days: int = 7) -> dict | None:
    """計算帳號 insights 的 N 天趨勢。數據不足時回傳 None。"""
    rows = conn.execute(
        "SELECT * FROM account_insights ORDER BY collected_date DESC LIMIT ?",
        (days,)
    ).fetchall()

    if len(rows) < 2:
        return None

    cols = [d[0] for d in conn.execute("SELECT * FROM account_insights LIMIT 0").description]
    latest = dict(zip(cols, rows[0]))
    oldest = dict(zip(cols, rows[-1]))

    trend = {}
    for key in ["followers", "total_views"]:
        old_val = oldest.get(key, 0)
        new_val = latest.get(key, 0)
        delta = new_val - old_val
        pct = (delta / old_val * 100) if old_val else 0
        trend[key] = {"value": new_val, "delta": delta, "pct": round(pct, 1)}

    trend["days"] = len(rows)
    return trend


def get_top_posts(conn: sqlite3.Connection, limit: int = 5) -> list[dict]:
    """取得觀看數最高的 N 篇貼文（最近一次 collected_date 的數據）。"""
    rows = conn.execute("""
        SELECT post_id, text_preview, posted_at, username, views, likes, replies, reposts, quotes
        FROM post_insights
        WHERE collected_date = (SELECT MAX(collected_date) FROM post_insights)
        ORDER BY views DESC
        LIMIT ?
    """, (limit,)).fetchall()

    cols = ["post_id", "text_preview", "posted_at", "username", "views", "likes", "replies", "reposts", "quotes"]
    return [dict(zip(cols, row)) for row in rows]


# ── Helper functions ───────────────────────────────────

def _calc_post_hour_local(posted_at: str, tz_name: str = "Asia/Taipei") -> int | None:
    """將 posted_at 轉換為本地時區的小時數（0-23）。"""
    if not posted_at:
        return None
    try:
        dt = datetime.fromisoformat(posted_at.replace("+0000", "+00:00"))
        tz = ZoneInfo(tz_name)
        return dt.astimezone(tz).hour
    except (ValueError, TypeError):
        return None


def _fetch_author_reply_count(post_id: str, username: str, token: str) -> int:
    """計算作者在該貼文下回覆了幾則。"""
    url = f"{THREADS_API_BASE}/{post_id}/replies"
    params = {
        "fields": "id,username",
        "access_token": token,
    }
    try:
        data = _request_with_retry(url, params)
        replies = data.get("data", [])
        return sum(1 for r in replies if r.get("username") == username)
    except Exception as e:
        logger.warning("取得貼文 %s 回覆數失敗: %s", post_id, e)
        return 0


# ── Private API helpers ─────────────────────────────────

def _fetch_all_posts(token: str) -> list[dict]:
    """用 me/threads 取得所有貼文（含分頁）。"""
    all_posts = []
    url = f"{THREADS_API_BASE}/me/threads"
    params = {
        "fields": "id,text,username,timestamp",
        "limit": 25,
        "access_token": token,
    }

    while url:
        data = _request_with_retry(url, params)
        posts = data.get("data", [])
        all_posts.extend(posts)

        # 分頁
        paging = data.get("paging", {})
        url = paging.get("next")
        params = {}  # next URL 已包含所有參數

        if len(all_posts) > 200:
            break  # 安全上限

    return all_posts


def _fetch_single_post_insights(post_id: str, token: str) -> dict:
    """抓單篇貼文的 insights。"""
    url = f"{THREADS_API_BASE}/{post_id}/insights"
    params = {
        "metric": "views,likes,replies,reposts,quotes",
        "access_token": token,
    }
    data = _request_with_retry(url, params)

    # 把 API 回傳的 metrics 展平成 dict
    result = {}
    for metric in data.get("data", []):
        name = metric["name"]
        values = metric.get("values", [])
        if values:
            result[name] = values[0].get("value", 0)
        else:
            result[name] = metric.get("total_value", {}).get("value", 0)

    return result


def _fetch_account_insights(token: str) -> dict:
    """抓帳號層級的 insights。"""
    url = f"{THREADS_API_BASE}/me/threads_insights"
    params = {
        "metric": "views,likes,replies,reposts,quotes,followers_count",
        "access_token": token,
    }
    data = _request_with_retry(url, params)

    result = {}
    for metric in data.get("data", []):
        name = metric["name"]
        if name == "followers_count":
            result["followers"] = metric.get("total_value", {}).get("value", 0)
        elif name == "views":
            values = metric.get("values", [])
            result["total_views"] = sum(v.get("value", 0) for v in values)
        else:
            result[f"total_{name}"] = metric.get("total_value", {}).get("value", 0)

    return result
