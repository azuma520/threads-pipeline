"""報告產出模組：Jinja2 渲染 Markdown + 存檔。"""

from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent / "templates"

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


def save_report(content: str, config: dict, report_date: str) -> str:
    """儲存報告至指定目錄，回傳檔案路徑。"""
    output_dir = Path(config["output"]["directory"])
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"threads_ai_trend_{report_date}.md"
    filepath = output_dir / filename

    filepath.write_text(content, encoding="utf-8")
    return str(filepath)
