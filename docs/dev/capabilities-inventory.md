# threads_pipeline 能力盤點

> 建立日期：2026-04-14
> 用途：skill/agent 規劃談資、功能 roadmap 參考、新成員 onboarding
> 維護：功能新增或重大變更時手動更新

專案依資料流分成四層，外加一個外部引用。

---

## Layer 1 — 資料採集（Threads API）

負責把外部資料拉進 SQLite。

| 能力 | 函式 | 出處 | 說明 |
|---|---|---|---|
| 關鍵字搜尋貼文 | `fetch_posts` | `threads_client.py:15` | 依 `config.yaml` keywords 搜尋；Standard Access 下僅回傳自己的貼文 |
| 抓單篇 insights | `fetch_and_store_post_insights` | `insights_tracker.py:108` | views / likes / replies / reposts / quotes / shares，upsert 進 SQLite |
| 抓帳號總數據 | `fetch_and_store_account_insights` | `insights_tracker.py:158` | follower_count / views / likes 等 |
| Token 驗證 | `validate_token` | `threads_client.py:119` | |
| Token 續期 | `refresh_token` | `threads_client.py:139` | 長效 token refresh |

**限制**：目前 Standard Access，`keyword_search` 只回自己貼文、`like_count` 不在搜尋結果（需走 `{post_id}/insights`）、中文關鍵字回 0 筆。Advanced Access 已送 App Review 等待核准。

---

## Layer 2 — 資料分析 & 查詢

讀 SQLite、做聚合與 LLM 分類。

| 能力 | 函式 | 出處 | 說明 |
|---|---|---|---|
| 批次貼文分類 | `analyze_posts` | `analyzer.py:33` | `claude -p --model haiku`，50 篇/批，失敗 fallback |
| 趨勢（漲跌幅） | `get_trend` | `db_helpers.py:46` | N 天 vs 前 N 天 |
| 爆文排行 | `get_top_posts` | `db_helpers.py:30` | 依 views 排序 |
| 最新帳號數據 | `get_account_latest` | `db_helpers.py:72` | |
| 發文時段分布 | `get_post_hour_distribution` | `db_helpers.py:85` | 每小時平均 views（找黃金時段）|
| 互動統計 | `get_engagement_stats` | `db_helpers.py:102` | |

---

## Layer 3 — 報告產出

Jinja2 模板渲染 → Markdown 檔。

| 報告 | 模板 | 輸出位置 | 觸發 |
|---|---|---|---|
| 趨勢日報 | `templates/daily_report.md.j2` | `output/threads_reports/trend/trend_YYYY-MM-DD.md` | `python -m threads_pipeline.main`（Job A）|
| 戰情日報 | `templates/dashboard_report.md.j2` | `output/threads_reports/dashboard/dashboard_YYYY-MM-DD.md` | `python -m threads_pipeline.main`（Job B）|
| 發文顧問分析 | `templates/advisor_report.md.j2` | `output/advisor/…` | `advisor analyze` |

核心函式：`report.render_report`、`report.render_dashboard`、`report.save_report`。

---

## Layer 4 — 發文顧問（advisor）

以 CLI 子指令提供個人化發文支援。進入點：`advisor.py`。

| 子指令 | 功能 | 關鍵邏輯 |
|---|---|---|
| `analyze` | 讀 SQLite → 產出「什麼時段好、什麼題材漲、爆文共通點」的分析報告 | `generate_analysis` (`advisor.py:59`)，模板 `advisor_report.md.j2` |
| `review` | 輸入草稿 → 呼叫 Codex / Claude 審查 → 給優化建議 | `_build_review_prompt` + `review_draft` (`advisor.py:211/239`) |
| `plan` | 輸入題目 → Stage 1（haiku）建議 3 框架 → Stage 2（sonnet）產出串文骨架 `plan.md` | `planner.generate_plan` (`planner.py:250`)，兩階段 prompt 分別在 `build_stage1_prompt` / `build_stage2_prompt` |
| `list-frameworks` | 列出 16+1 文案框架（含結構/適用場景） | `planner.list_frameworks` (`planner.py:55`) |

**輸入輸出**：
- `plan` 支援互動式（`_interactive_pick_framework`）與 `--auto`
- `plan` 產出路徑：`drafts/<timestamp>-<slug>.plan.md`
- `review` 支援 `--text` 直接傳字串 或 檔案路徑

**知識資產**：`references/copywriting-frameworks.md` — 16+1 文案框架完整定義（AIDA、PAS、FAB、HHH、BAB…）。

---

## 外部引用

| 資產 | 來源 | 提供什麼 |
|---|---|---|
| `threads-algorithm-skill` | `azuma520/threads-algorithm-skill` | 26 個 Meta 演算法專利機制（Creator Embedding、Audience Affinity、Diversity Enforcement、Low Signal 偵測…）|

---

## 能力覆蓋圖

```
          [Threads API]
                │
                ▼
        ┌───────────────┐
        │   Layer 1     │  採集 → SQLite
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │   Layer 2     │  查詢 + LLM 分析
        └───┬───────┬───┘
            │       │
            ▼       ▼
        ┌───────┐ ┌───────────────┐
        │Layer 3│ │   Layer 4     │
        │ 報告   │ │ advisor 發文   │ ← references/copywriting-frameworks.md
        └───────┘ │  analyze      │ ← threads-algorithm-skill (external)
                  │  review       │
                  │  plan         │
                  │  list-fw      │
                  └───────────────┘
```

---

## 未來 skill / agent 規劃待決

設計發文顧問 skill + agent 時，覆蓋範圍選項：

- **A. 只 Layer 4** — 純發文三件套（plan / review / analyze）
- **B. Layer 2 + 4** — 先讀自己的數據 → 決定要發什麼 → 產出草稿（完整閉環）
- **C. 全部四層** — 連資料採集都能觸發（「更新數據再給建議」）
- **D. Layer 2 + 3 + 4** — 分析 + 報告 + 發文，但不主動觸發 API 採集

決策時考量：哪些動作代價低（純讀 DB）、哪些代價高（打 API、花 LLM token），高代價動作是否該由 agent 自動觸發。
