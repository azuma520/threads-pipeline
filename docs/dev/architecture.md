# 架構設計

## 1. 產品定位

Threads AI Pipeline 是一套自建的社群經營戰情室，目的是讓個人帳號在不依賴第三方 SaaS 工具的情況下，取得和分析自己在 Threads 上的完整數據。

**核心痛點**：每天經營 Threads 但追蹤成效的方式是「打開 app 一篇篇看」，沒有統整分析，不知道什麼類型的內容有效、粉絲成長趨勢如何、什麼時間發文最好。

**終極目標（全自動循環）**：

```
收集趨勢 → AI 分析 → 建議發文 → 發文 → 追蹤成效 → 調整策略
```

目前版本（V2）完成「收集 + 分析 + 成效追蹤 + 戰情日報」四個核心環節，後續 V3 加入 AI 互動建議與自動發文。

---

## 2. Pipeline 流程圖

```
┌──────────────────────────────────────────────────────┐
│                  cron 排程觸發（每日）                  │
└──────────────────────────┬───────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│              main.py — 載入 config                    │
│  _load_dotenv()  →  load_config()                    │
│  解析 .env + config.yaml，${ENV_VAR} 插值             │
└──────────┬───────────────────────────────────────────┘
           │
           ├──────────────────────────────────────────┐
           │                                          │
           ▼                                          ▼
┌──────────────────────────┐          ┌──────────────────────────────┐
│  Job A: 趨勢收集          │          │  Job B: 成效追蹤              │
│  （獨立 try/except）       │          │  （獨立 try/except）           │
│                          │          │                              │
│  threads_client          │          │  insights_tracker.init_db()  │
│    .fetch_posts()        │          │                              │
│        │                 │          │  fetch_and_store_post        │
│        ▼                 │          │    _insights()               │
│  analyzer                │          │        │                     │
│    .analyze_posts()      │          │  fetch_and_store_account     │
│        │                 │          │    _insights()               │
│        ▼                 │          │        │                     │
│  report.render_report()  │          │  get_trend()                 │
│  report.save_report()    │          │  get_top_posts()             │
│  → trend_YYYY-MM-DD.md   │          │                              │
└──────────────────────────┘          └──────────────────────────────┘
           │                                          │
           └──────────────────┬───────────────────────┘
                              │
                              ▼
               ┌──────────────────────────────┐
               │  report.render_dashboard()   │
               │  report.save_report()        │
               │  → dashboard_YYYY-MM-DD.md   │
               └──────────────────────────────┘
```

Job A 與 Job B 各自包在獨立的 `try/except` 區塊內，任一 Job 失敗不會影響另一個；最終的戰情日報（dashboard）則在兩個 Job 執行完畢後合併輸出。

---

## 3. 模組職責

| 模組 | 職責 |
|------|------|
| `main.py` | Pipeline 進入點。負責載入 `.env` 與 `config.yaml`（含 `${ENV_VAR}` 插值），依序觸發 Job A / Job B，最後呼叫 `render_dashboard` 合併輸出戰情日報。 |
| `threads_client.py` | Threads Graph API 的 HTTP 封裝。實作關鍵字搜尋（`/keyword_search`）、分頁拉取自身貼文（`/me/threads`），以及指數退避重試的 `_request_with_retry`，供 `analyzer` 與 `insights_tracker` 共用。 |
| `analyzer.py` | 透過 `subprocess` 呼叫 `claude -p` 批次分析貼文（每批最多 50 篇），將每篇貼文分類為「新工具 / 產業動態 / 教學 / 觀點」並給予 1–5 分趨勢分數與中文摘要；Claude 分析失敗時自動 fallback 為預設值。 |
| `insights_tracker.py` | 從 Threads API 抓取貼文層級與帳號層級的 insights（觀看、按讚、回覆、轉發、引用、粉絲數），以 upsert 方式存入本地 SQLite；另提供 `get_trend` 計算 N 天趨勢、`get_top_posts` 取最高觀看貼文。 |
| `report.py` | 以 Jinja2 渲染兩種 Markdown 報告模板：`daily_report.md.j2`（趨勢日報，依分類分組排序）與 `dashboard_report.md.j2`（戰情日報，含帳號總覽、Top 5 貼文、互動率計算），並將結果存檔至設定的輸出目錄。 |

---

## 4. 關鍵設計決策

| 決策 | 選擇 | 原因 |
|------|------|------|
| AI 分析方式 | `claude -p` subprocess | 不額外接 API，用手邊有的最簡單方式 |
| 資料儲存 | SQLite | 比 CSV 查詢能力強，比外部 DB 不需額外設定 |
| Config 格式 | YAML + `${ENV_VAR}` 插值 | 可讀性好，secrets 不進版控 |
| 重複執行 | upsert (`ON CONFLICT DO UPDATE`) | 同一天重跑不會產生重複資料 |
| 錯誤隔離 | Job A / B 獨立 `try/except` | 趨勢收集失敗不影響成效追蹤 |
