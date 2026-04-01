"""報告產出模組：Jinja2 渲染 Markdown + 存檔。"""

from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent / "templates"


def _signdelta(value):
    """Jinja2 filter: +3 / -2 / 0"""
    if value > 0:
        return f"+{value}"
    return str(value)

# 分類顯示順序
CATEGORY_ORDER = ["新工具", "產業動態", "教學", "觀點"]


def render_report(posts: list[dict], report_date: str, config: dict) -> str:
    """渲染 Markdown 報告。"""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
    )
    template = env.get_template("daily_report.md.j2")

    # 按分類分組，組內按 score 降序
    posts_by_category = _group_and_sort(posts)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    keywords = config["threads"]["keywords"]
    model = config["anthropic"]["model"]

    return template.render(
        report_date=report_date,
        generated_at=generated_at,
        keywords=keywords,
        total_posts=len(posts),
        posts_by_category=posts_by_category,
        model=model,
    )


def _group_and_sort(posts: list[dict]) -> OrderedDict:
    """依 CATEGORY_ORDER 分組，組內按 score 降序排列。"""
    grouped: OrderedDict[str, list[dict]] = OrderedDict()

    for cat in CATEGORY_ORDER:
        cat_posts = [p for p in posts if p.get("category") == cat]
        if cat_posts:
            grouped[cat] = sorted(cat_posts, key=lambda p: p.get("score", 0), reverse=True)

    return grouped


def render_dashboard(
    account: dict,
    top_posts: list[dict],
    trend: dict | None,
    trend_post_count: int,
    report_date: str,
    config: dict,
) -> str:
    """渲染戰情日報。"""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
    )
    env.filters["signdelta"] = _signdelta
    template = env.get_template("dashboard_report.md.j2")

    tz_name = config.get("insights", {}).get("timezone", "UTC")
    tz = ZoneInfo(tz_name)
    generated_at = datetime.now(tz).strftime("%Y-%m-%d %H:%M")

    # 計算每篇貼文的互動率
    for p in top_posts:
        views = p.get("views", 0)
        if views > 0:
            engagement = p.get("likes", 0) + p.get("replies", 0) + p.get("reposts", 0) + p.get("quotes", 0)
            p["engagement_rate"] = round(engagement / views * 100, 1)
        else:
            p["engagement_rate"] = 0

        # 轉換發文時間到本地時區
        posted_at = p.get("posted_at", "")
        if posted_at:
            try:
                dt = datetime.fromisoformat(posted_at.replace("+0000", "+00:00"))
                p["posted_at_local"] = dt.astimezone(tz).strftime("%m/%d %H:%M")
            except (ValueError, TypeError):
                p["posted_at_local"] = posted_at[:16]
        else:
            p["posted_at_local"] = "—"

    return template.render(
        report_date=report_date,
        generated_at=generated_at,
        timezone=tz_name,
        username="azuma01130626",
        account=account,
        top_posts=top_posts,
        trend=trend,
        trend_post_count=trend_post_count,
    )


def save_report(
    content: str, config: dict, report_date: str,
    prefix: str = "threads_ai_trend", subdir: str = "",
) -> str:
    """儲存報告至指定目錄，回傳檔案路徑。"""
    raw_dir = config["output"]["directory"]
    output_dir = Path(raw_dir)
    if not output_dir.is_absolute():
        output_dir = Path(__file__).parent / raw_dir
    if subdir:
        output_dir = output_dir / subdir
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{prefix}_{report_date}.md"
    filepath = output_dir / filename

    filepath.write_text(content, encoding="utf-8")
    return str(filepath)
