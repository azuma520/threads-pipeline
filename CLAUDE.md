# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A daily pipeline that collects AI/tech trend posts from Meta Threads API, analyzes them with Claude CLI (`claude -p`), tracks account/post insights in SQLite, and generates Markdown reports via Jinja2 templates. Written in Traditional Chinese (繁體中文).

## Commands

```bash
# Run the pipeline (from parent directory 桌面/)
$env:PYTHONUTF8=1; python -m threads_pipeline.main   # PowerShell
PYTHONUTF8=1 python -m threads_pipeline.main          # bash

# Run all tests (from project root)
python -m pytest

# Run a single test file
python -m pytest tests/test_analyzer.py

# Run a specific test class or method
python -m pytest tests/test_analyzer.py::TestParseAnalysis::test_valid_json

# Run API exploration tests
python3 scripts/api_explorer.py

# Run advisor analyze (from parent directory 桌面/)
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor analyze
PYTHONUTF8=1 python -m threads_pipeline.advisor analyze

# Run advisor review (from parent directory 桌面/)
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor review drafts/my-post.txt
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor review --text "草稿文字"
```

## Project Structure

```
threads_pipeline/
├── .env                          # THREADS_ACCESS_TOKEN（gitignored）
├── config.yaml                   # 設定檔（${ENV_VAR} 插值）
├── main.py                       # Pipeline 入口
├── threads_client.py             # Threads API 封裝（搜尋、Token 驗證/續期）
├── analyzer.py                   # AI 分析（claude -p subprocess）
├── insights_tracker.py           # SQLite insights 追蹤
├── db_helpers.py                 # 共用 DB 連線與查詢
├── advisor.py                    # 發文顧問（analyze + review via Codex CLI）
├── report.py                     # Jinja2 報告渲染 + 存檔
├── references/
│   └── copywriting-frameworks.md # 16+1 爆款文案結構框架
├── templates/
│   ├── daily_report.md.j2        # 趨勢日報模板
│   ├── dashboard_report.md.j2    # 戰情日報模板
│   └── advisor_report.md.j2      # 發文顧問分析報告模板
├── tests/
│   ├── conftest.py
│   ├── test_analyzer.py
│   ├── test_threads_client.py
│   └── test_report.py
├── scripts/
│   ├── api_explorer.py           # API 功能邊界探索腳本
│   └── demo_publish_reply.py     # 發文/回覆 Demo（App Review 用）
├── output/threads_reports/
│   ├── trend/                    # 趨勢日報（trend_YYYY-MM-DD.md）
│   └── dashboard/                # 戰情日報（dashboard_YYYY-MM-DD.md）
├── docs/
│   ├── dev/                      # 開發文檔（架構、資料模型、測試、路線圖、API 探索）
│   └── legal/                    # 隱私政策、資料刪除說明（GitHub Pages）
└── assets/                       # App 圖示
```

## Architecture

The pipeline runs two independent jobs in sequence, each wrapped in its own try/except so one failure doesn't block the other:

**Job A — Trend Collection**: `threads_client.fetch_posts` (keyword search via Threads API with dedup) → `analyzer.analyze_posts` (batch `claude -p` subprocess calls, 50 posts/batch, with fallback on failure) → `report.render_report` (Jinja2 daily report)

**Job B — Insights Tracking**: `insights_tracker.fetch_and_store_post_insights` + `fetch_and_store_account_insights` (Threads insights API → SQLite upsert) → `get_trend` / `get_top_posts` (query SQLite) → `report.render_dashboard` (Jinja2 dashboard report)

### Key design decisions

- **AI analysis uses `claude -p` CLI subprocess**, not the Anthropic SDK. The analyzer shells out to `claude -p <prompt> --model haiku` and parses the JSON response.
- **Config uses `${ENV_VAR}` interpolation** — `main.load_config()` resolves environment variable references in `config.yaml` before YAML parsing. Secrets (like `THREADS_ACCESS_TOKEN`) come from `.env`.
- **SQLite upsert pattern** — `insights_tracker` uses `INSERT ... ON CONFLICT DO UPDATE` with `(collected_date, post_id)` as composite PK for post insights and `collected_date` as PK for account insights.
- **All HTTP requests** go through `threads_client._request_with_retry` with exponential backoff and 429 rate-limit handling.
- The package is imported as `threads_pipeline.*` (e.g., `from threads_pipeline.analyzer import ...`).
- **Must run from parent directory** — `python -m threads_pipeline.main` must be run from `桌面/`, not from inside `threads_pipeline/`.

### API Limitations (Standard Access)

Currently using Standard Access for `threads_keyword_search` — search results only contain the authenticated user's own posts. App Review submitted 2026-04-01 for Advanced Access. See `docs/dev/api-exploration-results.md` for full details.

- `keyword_search` actual limit is 50 (not 100 as documented)
- `like_count` not available in search results (use `{post_id}/insights` instead)
- `author_username` parameter ignored under Standard Access
- Chinese keyword search returns 0 results under Standard Access

## Available Skills

- **threads-algorithm-skill** (`/threads-algorithm-skill`) — Threads/Meta 社群經營顧問，基於 26 個 Meta 演算法專利機制，提供內容策略建議。來源：`azuma520/threads-algorithm-skill`

## Dependencies

- Python 3.13+
- requests, pyyaml, jinja2
- Claude Code CLI (for `claude -p` in analyzer)
- Meta Threads API access token in `.env`
