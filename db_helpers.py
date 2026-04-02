"""共用資料庫工具：config loading、DB 連線、基礎查詢。"""

import sqlite3
from pathlib import Path


def get_db_path(config: dict) -> Path:
    """從 config 取得 DB 檔案路徑。"""
    insights_cfg = config.get("insights", {})
    data_dir = Path(insights_cfg.get("data_dir", "./data"))
    db_name = insights_cfg.get("db_name", "threads.db")

    # 相對路徑以 CWD 為基準（與 insights_tracker.init_db 一致）
    if not data_dir.is_absolute():
        data_dir = Path.cwd() / data_dir

    return data_dir / db_name


def get_readonly_connection(config: dict) -> sqlite3.Connection:
    """取得 read-only DB 連線。"""
    db_path = get_db_path(config)
    if not db_path.exists():
        raise FileNotFoundError(f"資料庫不存在: {db_path}")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def get_top_posts(conn: sqlite3.Connection, limit: int = 5) -> list[dict]:
    """取得觀看數最高的 N 篇貼文（最近一次 collected_date）。"""
    rows = conn.execute("""
        SELECT post_id, text_preview, full_text, posted_at, post_hour_local,
               username, views, likes, replies, reposts, quotes, author_reply_count
        FROM post_insights
        WHERE collected_date = (SELECT MAX(collected_date) FROM post_insights)
        ORDER BY views DESC
        LIMIT ?
    """, (limit,)).fetchall()

    cols = ["post_id", "text_preview", "full_text", "posted_at", "post_hour_local",
            "username", "views", "likes", "replies", "reposts", "quotes", "author_reply_count"]
    return [dict(zip(cols, row)) for row in rows]


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


def get_account_latest(conn: sqlite3.Connection) -> dict:
    """取得最新一筆帳號 insights。"""
    row = conn.execute(
        "SELECT * FROM account_insights ORDER BY collected_date DESC LIMIT 1"
    ).fetchone()

    if not row:
        return {}

    cols = [d[0] for d in conn.execute("SELECT * FROM account_insights LIMIT 0").description]
    return dict(zip(cols, row))


def get_post_hour_distribution(conn: sqlite3.Connection, min_views: int = 100) -> dict[int, float]:
    """取得高表現貼文的發文時段分布。回傳 {hour: avg_engagement_rate}。"""
    rows = conn.execute("""
        SELECT post_hour_local,
               AVG(CASE WHEN views > 0 THEN (likes + replies + reposts + quotes) * 100.0 / views ELSE 0 END) as avg_rate,
               COUNT(*) as count
        FROM post_insights
        WHERE post_hour_local IS NOT NULL
          AND views >= ?
          AND collected_date = (SELECT MAX(collected_date) FROM post_insights)
        GROUP BY post_hour_local
        ORDER BY avg_rate DESC
    """, (min_views,)).fetchall()

    return {row[0]: round(row[1], 1) for row in rows}


def get_engagement_stats(conn: sqlite3.Connection) -> dict:
    """取得整體互動數據統計。"""
    row = conn.execute("""
        SELECT
            AVG(CASE WHEN views > 0 THEN (likes + replies + reposts + quotes) * 100.0 / views ELSE 0 END) as avg_engagement_rate,
            AVG(likes) as avg_likes,
            AVG(replies) as avg_replies,
            AVG(reposts) as avg_reposts,
            AVG(quotes) as avg_quotes,
            AVG(author_reply_count) as avg_author_replies,
            SUM(likes) as total_likes,
            SUM(replies) as total_replies,
            SUM(reposts) as total_reposts,
            COUNT(*) as post_count
        FROM post_insights
        WHERE collected_date = (SELECT MAX(collected_date) FROM post_insights)
          AND views > 0
    """).fetchone()

    if not row or row[0] is None:
        return {}

    total_interactions = (row[6] or 0) + (row[7] or 0) + (row[8] or 0)

    return {
        "avg_engagement_rate": round(row[0], 1),
        "avg_likes": round(row[1], 1),
        "avg_replies": round(row[2], 1),
        "avg_reposts": round(row[3], 1),
        "avg_author_replies": round(row[5], 1) if row[5] else 0,
        "like_pct": round(row[6] / total_interactions * 100, 0) if total_interactions else 0,
        "reply_pct": round(row[7] / total_interactions * 100, 0) if total_interactions else 0,
        "repost_pct": round(row[8] / total_interactions * 100, 0) if total_interactions else 0,
        "post_count": row[9],
    }
