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
    """Pipeline 主流程：收集 → 分析 → 報告。"""
    from threads_pipeline.threads_client import fetch_posts
    from threads_pipeline.analyzer import analyze_posts
    from threads_pipeline.report import render_report, save_report

    _load_dotenv()
    print("=== Threads AI 趨勢收集 Pipeline ===")

    # 載入設定
    config = load_config()
    print(f"✓ 設定載入完成（{len(config['threads']['keywords'])} 個關鍵字）")

    # 日期範圍：昨天 00:00 ~ 今天 00:00 UTC
    now = datetime.now(timezone.utc)
    report_date = now.strftime("%Y-%m-%d")

    # Step 1: 收集貼文
    print("\n--- Step 1: 資料收集 ---")
    posts = fetch_posts(config)
    print(f"✓ 共取得 {len(posts)} 篇貼文（去重後）")

    # Step 2: AI 分析
    if posts:
        print("\n--- Step 2: AI 分析 ---")
        posts = analyze_posts(posts, config)
        print(f"✓ 分析完成，共 {len(posts)} 篇")
    else:
        print("\n--- Step 2: 跳過（無貼文）---")

    # Step 3: 產出報告
    print("\n--- Step 3: 產出報告 ---")
    content = render_report(posts, report_date, config)
    filepath = save_report(content, config, report_date)
    print(f"✓ 報告已存檔：{filepath}")

    print("\n=== Pipeline 完成 ===")


if __name__ == "__main__":
    main()
