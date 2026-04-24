# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Session 開工規則

**每次 session 開始時，在回應用戶第一個任務之前，必須：**

1. **讀今日/最新 handoff 的「七、收工回寫」** — 看接力棒（上個 session 留言「下個 session 開工先做 X」）
   - 路徑：`docs/handoffs/session-handoff-{YYYYMMDD}.md`
   - 每天只有一份，每個 session 是一個 `## Session HH:MM` 區塊
2. **讀 memory** `project_progress_{YYYYMMDD}.md`（若存在）— Claude 跨 session 專用的進度摘要
3. 告訴用戶：「最新接力棒寫 X；要繼續還是先做你剛說的？」
4. 用戶決定優先級後再動手

不可以跳過這些步驟直接開工。

## Handoff 格式（每日 append-only）

**檔名**：`docs/handoffs/session-handoff-{YYYYMMDD}.md`

**規則**：同一天所有 session 寫在同一份檔案。每個 session 結束時 append 一個 `## Session HH:MM` 區塊。**禁止修改前面 session 的內容**。

每個 Session 區塊包含七個欄位：

| 欄位 | 必填？ | 寫什麼 | 不寫什麼 |
|------|--------|--------|---------|
| 一、今日聚焦 | ✅ | 今天要推進的主線項目 | — |
| 二、完成事項 | ✅ | 具體做了什麼，盡量量化 | 不寫過程流水帳 |
| 三、洞見紀錄 | 可「無」 | 過程中發現的心得、經驗（對人和 AI 都有用） | 不重複已存在的 memory |
| 四、阻塞/卡點 | 可「無」 | 想做但做不了的事 | — |
| 五、行動複盤 | 可「無」 | 工作方式/流程的改進反省 | 不寫自我感覺良好的廢話 |
| 六、檔案異動 | ✅ | 新增/搬移/刪除了什麼檔案 | 不列沒改的檔案 |
| 七、收工回寫 | ✅ | (1) `memory/project_progress_{YYYYMMDD}.md` 建立或更新；(2) `memory/MEMORY.md` 索引同步；(3) 下次 session 的 next action 提示 | — |

Stop hook 會擋：沒建檔、或最新 Session 區塊缺欄位，session 不准結束。

## 記憶系統與 handoff 的分工

- **handoff**（`docs/handoffs/`）：專案內、git 可追蹤、人讀用、append-only
- **memory**（`~/.claude/projects/.../memory/`）：跨專案 Claude 載入、指針式、可刪改
- 兩者互補，不是擇一。handoff 是「這天具體做了什麼」的人類紀錄；memory 是「下次 Claude 開 session 要記得的事」的 AI context

## Project Overview

A daily pipeline that collects AI/tech trend posts from Meta Threads API, analyzes them with Claude CLI (`claude -p`), tracks account/post insights in SQLite, and generates Markdown reports via Jinja2 templates. Written in Traditional Chinese (繁體中文).

## Commands

### 新版 CLI（推薦）

```bash
# 一次性安裝（開發模式）
pip install -e ".[dev]"

# Advisor
threads-advisor analyze
threads-advisor review drafts/x.txt
threads-advisor review --text "草稿文字"

# Threads API 操作（寫入指令預設 dry-run）
threads post publish "測試文字"                       # dry-run
threads post publish "測試文字" --confirm --yes       # 真發（Agent 模式）
threads reply add <post_id> "回覆內容" --confirm --yes
threads reply hide <reply_id>
threads reply unhide <reply_id>
threads account mentions
threads account mentions --json --limit 50
threads post publish-chain drafts/smoke-test.txt --confirm --yes

# profile_discovery（App Review 2026-04-23 送審中；endpoint pre-approval 回 400）
threads profile lookup https://www.threads.com/@username/post/SHORTCODE
threads profile posts username --limit 10

# 每日 pipeline（不 CLI 化）
$env:PYTHONUTF8=1; python -m threads_pipeline.main   # PowerShell
PYTHONUTF8=1 python -m threads_pipeline.main          # bash
```

### 舊版（相容性保留）

```bash
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor analyze
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor review drafts/my-post.txt
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor review --text "草稿文字"
```

### 測試

```bash
python -m pytest
python -m pytest tests/test_analyzer.py
python -m pytest tests/test_threads_cli.py
python3 scripts/api_explorer.py
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
- **threads-cli** — `threads` CLI 與 `threads-advisor` 操作手冊。Agent 執行 Threads 帳號操作（發文、查數據、刪文、審查草稿）時自動參考。Skill 檔案：`skills/threads-cli/SKILL.md`
- **threads-angle-gate** — C 路線第 1 層「選角度 Gate」草案。使用者要寫 Threads 貼文但還沒想清楚切入點時用；訪談者+共創者模式，AI 只用「發問」和「總結+詢問」兩種發言形式，產出 `drafts/<slug>.angle.md`。Skill 檔案：`skills/threads-angle-gate/SKILL.md`

## Dependencies

- Python 3.13+
- requests, pyyaml, jinja2
- Claude Code CLI (for `claude -p` in analyzer)
- Meta Threads API access token in `.env`
