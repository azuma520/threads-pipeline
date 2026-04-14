"""發文顧問模組：數據分析 + Codex CLI 草稿審查。"""

import json
import logging
import os
import subprocess
import sys
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

def load_config():
    """延遲匯入 load_config，允許測試 monkeypatch。"""
    from threads_pipeline.main import load_config as _load_config
    return _load_config()


# 可被 ADVISOR_* 環境變數覆寫（Layer 3 eval 與使用者自訂用）
FRAMEWORKS_MD_PATH = os.environ.get(
    "ADVISOR_FRAMEWORKS_MD",
    str(Path(__file__).parent.parent / "references" / "copywriting-frameworks.md"),
)
DRAFTS_DIR = os.environ.get(
    "ADVISOR_DRAFTS_DIR",
    str(Path(__file__).parent.parent / "drafts"),
)


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


REVIEW_PROMPT_TEMPLATE = """你是一位 Threads 社群經營顧問，負責審查以下草稿。

## 審查標準（6 個維度）

1. 鉤子 — 前兩行能不能讓人停下來（前 3 秒抓住眼球）
2. 聚焦度 — 一篇一個切入點、一種人、一個問題
3. Takeaway — 讀完能帶走什麼，會不會想回覆
4. 定位一致性 — 跟歷史高表現內容方向是否一致
5. 受眾匹配 — 有沒有打中目標受眾的痛點{audience_note}
6. 結構完整性 — 是否符合文案結構要素，結尾是否有力{structure_note}

## 帳號數據摘要
{analysis_summary}

{plan_section}

## 待審查草稿
---
{draft}
---

請輸出：
1. 整體評分（1-5 星）
2. 每個維度用 ✅ / ⚠️ / ❌ 標記，加一句說明
3. 3-5 個具體的「建議行動」

用繁體中文回答。只輸出審查結果，不要重複草稿內容。"""


def _build_review_prompt(
    draft: str,
    analysis_json: dict,
    plan_content: str | None = None,
) -> str:
    """組合審查 prompt，控制在 8000 字以內。"""
    analysis_summary = json.dumps(analysis_json, ensure_ascii=False, indent=2) if analysis_json else "（無數據）"

    if plan_content:
        plan_section = f"## 發文規劃\n{plan_content[:4000]}"
        audience_note = "（參考發文規劃中的受眾設定）"
        structure_note = "（參考發文規劃中的建議結構）"
    else:
        plan_section = ""
        audience_note = "（無發文規劃，跳過此維度）"
        structure_note = "（無發文規劃，僅檢查基本結構）"

    prompt = REVIEW_PROMPT_TEMPLATE.format(
        analysis_summary=analysis_summary[:2000],
        plan_section=plan_section,
        draft=draft[:3000],
        audience_note=audience_note,
        structure_note=structure_note,
    )

    return prompt


def review_draft(
    draft: str,
    analysis_json: dict | None = None,
    plan_content: str | None = None,
    timeout: int = 60,
) -> str:
    """用 Codex CLI 審查草稿。回傳審查結果字串。"""
    prompt = _build_review_prompt(
        draft=draft,
        analysis_json=analysis_json or {},
        plan_content=plan_content,
    )

    import platform
    use_shell = platform.system() == "Windows"

    try:
        result = subprocess.run(
            ["codex", "exec", "-s", "read-only", "-"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            shell=use_shell,
        )

        if result.returncode != 0:
            logger.warning("Codex 審查失敗 (exit %d): %s", result.returncode, result.stderr)
            return f"審查失敗（Codex exit code {result.returncode}）。請手動檢查草稿。\n\nstderr: {result.stderr[:500]}"

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        logger.warning("Codex 審查超時 (%ds)", timeout)
        return f"審查失敗（超時 {timeout} 秒）。請手動檢查草稿。"
    except FileNotFoundError:
        return "審查失敗：找不到 codex CLI。請確認已安裝。"


# ── CLI 入口 ─────────────────────────────────────────────

import argparse


def main():
    parser = argparse.ArgumentParser(description="Threads 發文顧問")
    subparsers = parser.add_subparsers(dest="command")

    # analyze
    analyze_parser = subparsers.add_parser("analyze", help="產生數據分析報告")
    analyze_parser.add_argument("--date", default=None, help="報告日期 (YYYY-MM-DD)")

    # review
    review_parser = subparsers.add_parser("review", help="審查草稿")
    review_parser.add_argument("file", nargs="?", help="草稿檔案路徑")
    review_parser.add_argument("--text", help="直接輸入草稿文字")
    review_parser.add_argument("--plan", help="指定 plan 檔案路徑")
    review_parser.add_argument("--analysis", help="指定 analysis JSON 路徑")

    # plan
    plan_parser = subparsers.add_parser("plan", help="產生串文骨架 plan.md")
    plan_parser.add_argument("topic", nargs="?", help="題目（引號包起來）")
    plan_parser.add_argument("--topic-file", help="從檔案讀題目（避免 shell 跳脫問題）")
    plan_parser.add_argument("--framework", help="強制指定框架編號或名稱")
    plan_parser.add_argument("--auto", action="store_true", help="跳過互動，用 LLM 第一推薦")
    plan_parser.add_argument("--format", choices=["thread", "single"], help="預設 thread")
    plan_parser.add_argument("--style-posts", type=int, help="風格範本條數，預設 3")
    plan_parser.add_argument("--model", help="覆寫 Stage 2 模型（預設 sonnet）")
    plan_parser.add_argument("--suggest-only", action="store_true", help="只跑 Stage 1 回建議")
    plan_parser.add_argument("--json", action="store_true", help="結果以 JSON 輸出 (stdout)")
    overwrite_group = plan_parser.add_mutually_exclusive_group()
    overwrite_group.add_argument("--overwrite", action="store_true", help="檔案已存在直接覆寫")
    overwrite_group.add_argument("--no-overwrite", action="store_true", help="檔案已存在即報錯")

    # list-frameworks
    list_parser = subparsers.add_parser("list-frameworks", help="列出 16+1 框架")
    list_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.command == "analyze":
        _cmd_analyze(args)
    elif args.command == "review":
        _cmd_review(args)
    elif args.command == "plan":
        sys.exit(_cmd_plan(args))
    elif args.command == "list-frameworks":
        sys.exit(_cmd_list_frameworks(args))
    else:
        parser.print_help()


def _cmd_analyze(args):
    """執行 analyze 子指令。"""
    from threads_pipeline.main import _load_dotenv, load_config
    from threads_pipeline.db_helpers import get_readonly_connection
    from threads_pipeline.insights_tracker import init_db

    _load_dotenv()
    config = load_config()

    report_date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 先跑 migration 確保 schema 是最新的
    try:
        migration_conn = init_db(config)
        migration_conn.close()
    except Exception:
        pass

    try:
        conn = get_readonly_connection(config)
    except FileNotFoundError as e:
        print(f"✗ {e}")
        print("  請先執行 Pipeline 收集數據")
        return

    # 產生報告
    report = generate_analysis(conn, report_date)

    # 產生 JSON 摘要
    analysis_json = generate_analysis_json(conn)
    conn.close()

    # 存檔
    output_dir = Path(__file__).parent / "output" / "advisor"
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / f"analysis_{report_date}.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"✓ 分析報告：{report_path}")

    json_path = output_dir / f"analysis_{report_date}.json"
    json_path.write_text(json.dumps(analysis_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ 審查摘要：{json_path}")


def _cmd_review(args):
    """執行 review 子指令。"""
    # 讀取草稿
    if args.file:
        draft_path = Path(args.file)
        if not draft_path.exists():
            print(f"✗ 找不到草稿檔案: {draft_path}")
            return
        draft = draft_path.read_text(encoding="utf-8")
        topic_id = draft_path.stem
    elif args.text:
        draft = args.text
        topic_id = "inline"
    else:
        print("✗ 請提供草稿檔案或 --text 參數")
        return

    if not draft.strip():
        print("✗ 草稿為空")
        return

    if len(draft) > 2000:
        print(f"⚠ 草稿偏長（{len(draft)} 字），建議精簡到 2000 字以內")

    # 讀取 analysis JSON
    analysis_json = {}
    if args.analysis:
        analysis_path = Path(args.analysis)
    else:
        # 自動找最新的
        advisor_dir = Path(__file__).parent / "output" / "advisor"
        json_files = sorted(advisor_dir.glob("analysis_*.json"), reverse=True)
        analysis_path = json_files[0] if json_files else None

    if analysis_path and analysis_path.exists():
        analysis_json = json.loads(analysis_path.read_text(encoding="utf-8"))
        print(f"✓ 讀取分析摘要：{analysis_path}")
    else:
        print("⚠ 找不到分析摘要，跳過數據維度")

    # 讀取 plan
    plan_content = None
    if args.plan:
        plan_path = Path(args.plan)
    else:
        # 自動找同名 plan
        plan_path = Path(f"drafts/{topic_id}.plan.md")

    if plan_path and plan_path.exists():
        plan_content = plan_path.read_text(encoding="utf-8")
        print(f"✓ 讀取發文規劃：{plan_path}")
    else:
        print("⚠ 找不到發文規劃，跳過受眾匹配和結構完整性維度")

    # 審查
    print("\n正在審查草稿（Codex CLI）...")
    result = review_draft(draft, analysis_json, plan_content)
    print("\n" + result)

    # 存檔
    if args.file:
        review_path = Path(f"drafts/{topic_id}.review.md")
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(result, encoding="utf-8")
        print(f"\n✓ 審查結果：{review_path}")


def _get_db_connection_for_plan(config: dict):
    """取得 DB 連線，優先使用 config['storage']['sqlite_path']（eval 隔離用）。"""
    import sqlite3

    storage = config.get("storage", {})
    sqlite_path = storage.get("sqlite_path")
    if sqlite_path:
        p = Path(sqlite_path)
        if not p.exists():
            raise FileNotFoundError(f"資料庫不存在: {p}")
        conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    from threads_pipeline.db_helpers import get_readonly_connection
    return get_readonly_connection(config)


def _cmd_plan(args) -> int:
    """plan 子指令入口。回傳 exit code（給 main() sys.exit 用）。"""
    from threads_pipeline import planner
    from threads_pipeline.main import _load_dotenv
    from threads_pipeline.db_helpers import get_top_posts
    import sys as _sys

    _load_dotenv()
    config = load_config()

    # 讀題目
    topic = args.topic
    if args.topic_file:
        topic_path = Path(args.topic_file)
        if not topic_path.exists():
            print(f"✗ 找不到題目檔案：{topic_path}", file=_sys.stderr)
            return 1
        topic = topic_path.read_text(encoding="utf-8").strip()
    if not topic:
        print("✗ 請提供題目（引號字串或 --topic-file）", file=_sys.stderr)
        return 1

    # 讀 frameworks md
    fw_md = Path(FRAMEWORKS_MD_PATH).read_text(encoding="utf-8")

    # 解析 --framework（支援編號或名稱）
    framework_arg: int | str | None = None
    if args.framework:
        try:
            framework_arg = int(args.framework)
        except ValueError:
            framework_arg = args.framework
        section = planner.extract_framework_section(fw_md, framework_arg)
        if section is None:
            print(f"✗ 未知框架：{args.framework}", file=_sys.stderr)
            print("合法選項：", file=_sys.stderr)
            for fw in planner.list_frameworks(fw_md):
                print(f"  {fw['id']:02d} {fw['name']}", file=_sys.stderr)
            return 1

    # resolve config
    plan_cfg = planner.resolve_plan_config(
        config, cli_model=args.model, cli_style_posts=args.style_posts, cli_format=args.format,
    )

    # --suggest-only
    if args.suggest_only:
        try:
            suggestions = planner.suggest_frameworks(topic=topic, frameworks_md=fw_md)
        except planner.PlannerError as e:
            print(f"✗ {e}", file=_sys.stderr)
            return 3
        if args.json:
            import json as _json
            print(_json.dumps({"suggestions": suggestions}, ensure_ascii=False))
        else:
            for s in suggestions:
                print(f"[{s['rank']}] {s['framework']:02d} {s['name']}", file=_sys.stderr)
                print(f"    {s['reason']}", file=_sys.stderr)
        return 0

    # 讀 top posts
    try:
        conn = _get_db_connection_for_plan(config)
    except FileNotFoundError:
        if plan_cfg["style_posts"] > 0:
            print("⚠ 找不到 SQLite，風格範本將為空", file=_sys.stderr)
        top_posts = []
    else:
        raw_posts = get_top_posts(conn, limit=plan_cfg["style_posts"])
        conn.close()
        top_posts = []
        for p in raw_posts:
            views = p.get("views", 0)
            eng = p.get("likes", 0) + p.get("replies", 0) + p.get("reposts", 0) + p.get("quotes", 0)
            rate = round(eng / views * 100, 1) if views > 0 else 0
            top_posts.append({"full_text": p.get("full_text", ""), "engagement_rate": rate})
        if len(top_posts) < plan_cfg["style_posts"]:
            print(f"⚠ top posts 僅 {len(top_posts)} 篇（預期 {plan_cfg['style_posts']}）", file=_sys.stderr)

    # 決定 interactive vs auto
    is_tty = _sys.stdin.isatty()
    chosen_fw: int | str | None = None
    auto = args.auto
    if framework_arg is None and not auto:
        if not is_tty:
            print("⚠ stdin 非 tty，自動等同 --auto", file=_sys.stderr)
            auto = True
        else:
            chosen_fw = _interactive_pick_framework(topic=topic, frameworks_md=fw_md)
            if chosen_fw is None:
                print("✗ 已取消", file=_sys.stderr)
                return 2

    # 生骨架
    try:
        plan_md, used = planner.generate_plan(
            topic=topic,
            frameworks_md=fw_md,
            top_posts=top_posts,
            framework=framework_arg,
            fmt=plan_cfg["format"],
            stage2_model=plan_cfg["stage2_model"],
            auto=auto,
            chosen_framework=chosen_fw,
        )
    except planner.PlannerError as e:
        msg = str(e)
        print(f"✗ {msg}", file=_sys.stderr)
        if "JSON" in msg or "解析" in msg or "超時" in msg or "claude" in msg:
            return 3
        return 1

    # 寫檔
    slug = planner.slugify(topic)
    drafts_dir = Path(DRAFTS_DIR)
    drafts_dir.mkdir(parents=True, exist_ok=True)
    out_path = drafts_dir / f"{slug}.plan.md"

    if out_path.exists():
        if args.no_overwrite:
            print(f"✗ 檔案已存在：{out_path}（--no-overwrite）", file=_sys.stderr)
            return 4
        if not args.overwrite and is_tty:
            ans = input(f"覆寫 {out_path}？ [y/N] ").strip().lower()
            if ans != "y":
                print("✗ 已取消（檔案未改變）", file=_sys.stderr)
                return 2

    out_path.write_text(plan_md, encoding="utf-8")
    print(f"✓ plan.md 已寫入：{out_path}（框架 {used:02d}）", file=_sys.stderr)
    print(str(out_path))  # stdout: path for agent consumption
    return 0


def _interactive_pick_framework(topic: str, frameworks_md: str) -> int | str | None:
    """暫時用 auto 行為；Task 8b 會替換為真正的互動 UI。"""
    from threads_pipeline import planner
    suggestions = planner.suggest_frameworks(topic=topic, frameworks_md=frameworks_md)
    return suggestions[0]["framework"] if suggestions else None


def _cmd_list_frameworks(args) -> int:
    """list-frameworks 子指令。"""
    from threads_pipeline import planner
    import sys as _sys

    fw_md = Path(FRAMEWORKS_MD_PATH).read_text(encoding="utf-8")
    frameworks = planner.list_frameworks(fw_md)
    if args.json:
        import json as _json
        print(_json.dumps(frameworks, ensure_ascii=False, indent=2))
    else:
        for fw in frameworks:
            print(f"{fw['id']:02d} {fw['name']}")
            print(f"   公式：{fw['formula']}")
            print(f"   適用：{fw['when_to_use']}")
            print()
    return 0


if __name__ == "__main__":
    main()
