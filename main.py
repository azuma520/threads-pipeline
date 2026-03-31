"""Threads AI 趨勢收集 Pipeline — 每日自動收集、分析、產出報告。"""

import os
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

# Windows 中文輸出
os.environ.setdefault("PYTHONUTF8", "1")

CONFIG_PATH = Path(__file__).parent / "config.yaml"
ENV_PATH = Path(__file__).parent / ".env"


def _load_dotenv(path: Path = ENV_PATH):
    """讀取 .env 檔案，載入環境變數（不覆蓋已存在的）。"""
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            os.environ.setdefault(key, value)


def load_config(path: Path = CONFIG_PATH) -> dict:
    """讀取 config.yaml，解析 ${ENV_VAR} 格式的環境變數引用。"""
    with open(path, encoding="utf-8") as f:
        raw = f.read()

    # 替換 ${VAR_NAME} → os.environ[VAR_NAME]
    def _resolve_env(match):
        var_name = match.group(1)
        value = os.environ.get(var_name)
        if value is None:
            print(f"⚠ 環境變數 {var_name} 未設定，使用空字串")
            return ""
        return value

    resolved = re.sub(r"\$\{(\w+)\}", _resolve_env, raw)
    return yaml.safe_load(resolved)


def main():
    """Pipeline 主流程：趨勢收集 + 成效追蹤，各自獨立不互相拖累。"""
    from threads_pipeline.threads_client import fetch_posts
    from threads_pipeline.analyzer import analyze_posts
    from threads_pipeline.report import render_report, render_dashboard, save_report
    from threads_pipeline.insights_tracker import (
        init_db, fetch_and_store_post_insights,
        fetch_and_store_account_insights, get_trend, get_top_posts,
    )

    _load_dotenv()
    print("=== Threads 社群經營戰情室 V2 ===")

    config = load_config()
    print(f"✓ 設定載入完成（{len(config['threads']['keywords'])} 個關鍵字）")

    now = datetime.now(timezone.utc)
    report_date = now.strftime("%Y-%m-%d")

    # ── Job A: 趨勢收集（獨立 try/except）──
    trend_report = ""
    try:
        print("\n--- Job A: 趨勢收集 ---")
        posts = fetch_posts(config)
        print(f"  取得 {len(posts)} 篇貼文（去重後）")

        if posts:
            posts = analyze_posts(posts, config)
            print(f"  AI 分析完成，共 {len(posts)} 篇")

        trend_content = render_report(posts, report_date, config)
        trend_path = save_report(trend_content, config, report_date, prefix="trend")
        print(f"✓ 趨勢日報已存檔：{trend_path}")
        trend_report = trend_content
    except Exception as e:
        print(f"✗ 趨勢收集失敗：{e}")

    # ── Job B: 成效追蹤（獨立 try/except）──
    account_data = {}
    top_posts = []
    trend_data = None
    try:
        print("\n--- Job B: 成效追蹤 ---")
        conn = init_db(config)

        post_count = fetch_and_store_post_insights(config, conn)
        print(f"  {post_count} 篇貼文 insights 已存入 SQLite")

        account_data = fetch_and_store_account_insights(config, conn)
        print(f"  帳號 insights 已存入（粉絲: {account_data.get('followers', '?')}）")

        trend_data = get_trend(conn)
        top_posts = get_top_posts(conn)
        conn.close()
        print("✓ 成效追蹤完成")
    except Exception as e:
        print(f"✗ 成效追蹤失敗：{e}")

    # ── 合併戰情日報 ──
    print("\n--- 產出戰情日報 ---")
    if account_data:
        dashboard = render_dashboard(
            account=account_data,
            top_posts=top_posts,
            trend=trend_data,
            trend_report=trend_report,
            report_date=report_date,
            config=config,
        )
        dash_path = save_report(dashboard, config, report_date, prefix="dashboard")
        print(f"✓ 戰情日報已存檔：{dash_path}")
    else:
        print("⚠ 無帳號數據，跳過戰情日報")

    print("\n=== Pipeline 完成 ===")


if __name__ == "__main__":
    main()
