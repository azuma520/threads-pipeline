"""發文顧問模組：數據分析 + Codex CLI 草稿審查。"""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from threads_pipeline.db_helpers import (
    get_account_latest,
    get_engagement_stats,
    get_post_hour_distribution,
    get_top_posts,
    get_trend,
)

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


def _signdelta(value):
    """Jinja2 filter：正數加 + 號。"""
    if value > 0:
        return f"+{value}"
    return str(value)


def _posted_at_to_local(posted_at: str) -> str:
    """將 Threads API 的 posted_at 轉換為 UTC+8 本地時間字串。"""
    try:
        dt = datetime.fromisoformat(posted_at.replace("+0000", "+00:00"))
        local_dt = dt + timedelta(hours=8)
        return local_dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError, AttributeError):
        return posted_at or "N/A"


def generate_analysis(conn, report_date: str, username: str = "azuma01130626") -> str:
    """產生分析報告 Markdown。根據數據量自動選擇模式。"""
    account = get_account_latest(conn)
    top_posts = get_top_posts(conn, limit=10)

    # 判斷模式
    if not account and not top_posts:
        mode = "no_data"
    elif not get_trend(conn):
        mode = "degraded"
    else:
        mode = "normal"

    # 計算互動率
    for p in top_posts:
        views = p.get("views", 0)
        if views > 0:
            engagement = p.get("likes", 0) + p.get("replies", 0) + p.get("reposts", 0) + p.get("quotes", 0)
            p["engagement_rate"] = round(engagement / views * 100, 1)
        else:
            p["engagement_rate"] = 0

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), keep_trailing_newline=True)
    env.filters["signdelta"] = _signdelta
    template = env.get_template("advisor_report.md.j2")

    # 準備模板數據
    context = {
        "report_date": report_date,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "username": username,
        "mode": mode,
        "account": account,
        "top_posts": top_posts[:5],
    }

    if mode == "normal":
        trend = get_trend(conn)
        stats = get_engagement_stats(conn)
        hour_dist = get_post_hour_distribution(conn)
        bottom_posts = sorted(top_posts, key=lambda p: p.get("views", 0))

        # 按時間排序找最近的
        time_sorted = sorted(top_posts, key=lambda p: p.get("posted_at", ""), reverse=True)
        last_post = time_sorted[0] if time_sorted else {}
        days_since = 0
        if last_post.get("posted_at"):
            try:
                posted_dt = datetime.fromisoformat(last_post["posted_at"].replace("+0000", "+00:00"))
                days_since = (datetime.now(timezone.utc) - posted_dt).days
            except (ValueError, TypeError):
                days_since = 0

        # 為 last_post 加入本地時間
        last_post["posted_at_local"] = _posted_at_to_local(last_post.get("posted_at", ""))

        if days_since > 3:
            freshness = "已過期，建議先暖場再發文"
        elif days_since > 1:
            freshness = "冷卻中，可以發文"
        else:
            freshness = "仍在 freshness 週期內"

        context.update({
            "trend": trend,
            "stats": stats,
            "hour_distribution": dict(list(hour_dist.items())[:5]),
            "bottom_posts": bottom_posts[:3],
            "last_post": last_post,
            "days_since_last": days_since,
            "freshness_status": freshness,
        })

    return template.render(**context)


def generate_analysis_json(conn) -> dict:
    """產生分析摘要 JSON（供 review 使用，控制 prompt 長度）。"""
    account = get_account_latest(conn)
    stats = get_engagement_stats(conn)
    hour_dist = get_post_hour_distribution(conn)
    top_posts = get_top_posts(conn, limit=5)
    trend = get_trend(conn)

    # Top 關鍵字（從 full_text 簡單提取）
    keywords = {}
    for p in top_posts:
        text = p.get("full_text", "") or ""
        for kw in ["AI", "Claude", "GPT", "Agent", "自動化", "工具", "經驗", "學習"]:
            if kw in text:
                keywords[kw] = keywords.get(kw, 0) + 1

    top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)

    # 最近一篇
    time_sorted = sorted(top_posts, key=lambda p: p.get("posted_at", ""), reverse=True)
    last_post = time_sorted[0] if time_sorted else {}
    days_since = 0
    if last_post.get("posted_at"):
        try:
            posted_dt = datetime.fromisoformat(last_post["posted_at"].replace("+0000", "+00:00"))
            days_since = (datetime.now(timezone.utc) - posted_dt).days
        except (ValueError, TypeError):
            pass

    return {
        "followers": account.get("followers", 0),
        "total_views": account.get("total_views", 0),
        "trend_days": trend["days"] if trend else 0,
        "follower_delta": trend["followers"]["delta"] if trend else 0,
        "avg_engagement_rate": stats.get("avg_engagement_rate", 0),
        "like_pct": stats.get("like_pct", 0),
        "reply_pct": stats.get("reply_pct", 0),
        "repost_pct": stats.get("repost_pct", 0),
        "avg_author_replies": stats.get("avg_author_replies", 0),
        "top_post_hours": list(hour_dist.keys())[:3],
        "top_content_keywords": [kw for kw, _ in top_keywords[:5]],
        "last_post_days_ago": days_since,
        "freshness": "expired" if days_since > 3 else "cooling" if days_since > 1 else "active",
        "post_count": stats.get("post_count", 0),
    }
