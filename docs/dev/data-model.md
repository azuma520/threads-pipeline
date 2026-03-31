# 資料模型

本文件說明 Threads AI Pipeline 的 SQLite schema、追蹤指標定義、設定檔結構，以及一筆貼文在 pipeline 各階段的欄位演變。

---

## 1. SQLite Schema

資料庫存放於 `config.yaml` 的 `insights.data_dir` 目錄下，檔案名稱由 `insights.db_name` 決定（預設 `./data/threads.db`）。資料庫包含兩張表，以下為完整欄位定義。

### 1.1 `post_insights` — 貼文成效

| 欄位 | 型別 | 說明 |
|------|------|------|
| `collected_date` | TEXT NOT NULL | 收集日期，格式 `YYYY-MM-DD`（UTC） |
| `post_id` | TEXT NOT NULL | Threads 貼文 ID |
| `text_preview` | TEXT | 貼文前 50 字（換行轉空白） |
| `posted_at` | TEXT | 貼文發佈時間（ISO 8601，來自 API `timestamp`） |
| `username` | TEXT | 發文帳號名稱 |
| `views` | INTEGER DEFAULT 0 | 觀看數 |
| `likes` | INTEGER DEFAULT 0 | 按讚數 |
| `replies` | INTEGER DEFAULT 0 | 留言數 |
| `reposts` | INTEGER DEFAULT 0 | 轉發數 |
| `quotes` | INTEGER DEFAULT 0 | 引用數 |

**Primary Key：`(collected_date, post_id)`**

### 1.2 `account_insights` — 帳號成效

| 欄位 | 型別 | 說明 |
|------|------|------|
| `collected_date` | TEXT NOT NULL | 收集日期，格式 `YYYY-MM-DD`（UTC） |
| `followers` | INTEGER DEFAULT 0 | 當日粉絲數 |
| `total_views` | INTEGER DEFAULT 0 | 當日全帳號總觀看數（所有貼文加總） |
| `total_likes` | INTEGER DEFAULT 0 | 當日全帳號總按讚數 |
| `total_replies` | INTEGER DEFAULT 0 | 當日全帳號總留言數 |
| `total_reposts` | INTEGER DEFAULT 0 | 當日全帳號總轉發數 |

**Primary Key：`collected_date`**

### 1.3 Upsert 策略

兩張表均採用 SQLite `INSERT ... ON CONFLICT ... DO UPDATE SET` 語法（即 upsert）：

- **`post_insights`**：衝突條件為 `(collected_date, post_id)`。同一天對同一篇貼文重新執行 pipeline，會更新 `views`、`likes`、`replies`、`reposts`、`quotes`，不會插入重複列。`text_preview`、`posted_at`、`username` 維持首次寫入的值。
- **`account_insights`**：衝突條件為 `collected_date`。同一天重跑會覆寫所有數值欄位（`followers`、`total_views`、`total_likes`、`total_replies`、`total_reposts`）。

這個設計確保每天只保留一份最新快照，重跑不會造成資料重複，也不需要先刪後插。

---

## 2. 追蹤指標

| 指標 | 計算方式 | 來源 | 用途 |
|------|----------|------|------|
| 每篇觀看數 | `views`（直接讀取） | `post_insights` | 找出爆文模式 |
| 互動率 | `(likes + replies + reposts + quotes) / views * 100` | `post_insights` | 內容品質指標 |
| 粉絲數變化 | `latest.followers - oldest.followers` | `account_insights` 最近 N 筆 | 成長趨勢 |
| 每日總觀看 | `total_views`（直接讀取） | `account_insights` | 整體曝光趨勢 |
| N 天趨勢 | `get_trend(conn, days=7)` | `account_insights` 最近 N 筆 | 趨勢方向和百分比 |

### 2.1 N 天趨勢（`get_trend`）

`get_trend(conn, days=N)` 從 `account_insights` 取最近 N 筆資料（依 `collected_date` 降冪排列），比較最新一筆與最舊一筆的差值：

```
delta = latest[key] - oldest[key]
pct   = delta / oldest[key] * 100  （oldest 為 0 時 pct = 0）
```

目前計算 `followers` 與 `total_views` 兩個指標。回傳格式：

```json
{
  "followers":    { "value": 1280, "delta": 45, "pct": 3.6 },
  "total_views":  { "value": 98000, "delta": 12000, "pct": 14.0 },
  "days": 7
}
```

資料不足 2 筆時回傳 `None`。

### 2.2 Top N 貼文（`get_top_posts`）

`get_top_posts(conn, limit=5)` 取最近一次 `collected_date` 的貼文，依 `views` 降冪排列，回傳前 N 筆。各筆包含欄位：`post_id`、`text_preview`、`posted_at`、`username`、`views`、`likes`、`replies`、`reposts`、`quotes`。

---

## 3. `config.yaml` 說明

設定檔分為四個區塊，說明如下。

### 3.1 `threads` 區塊

| 欄位 | 預設值 | 說明 |
|------|--------|------|
| `access_token` | `${THREADS_ACCESS_TOKEN}` | Threads Graph API 的存取金鑰，透過環境變數注入 |
| `keywords` | `[AI, LLM, Claude, ...]` | 搜尋關鍵字清單，每個關鍵字獨立呼叫一次 API |
| `sort` | `"TOP"` | 搜尋排序方式，傳入 Threads API 的 `sort` 參數（`TOP` 或 `RECENT`） |
| `max_posts_per_keyword` | `25` | 每個關鍵字最多取幾篇貼文（Threads API 單次上限為 25） |

### 3.2 `anthropic` 區塊

| 欄位 | 預設值 | 說明 |
|------|--------|------|
| `model` | `"claude-sonnet-4-6"` | 報告產出使用的 Claude 模型 ID（report.py 使用） |
| `max_tokens` | `2048` | 單次 API 呼叫最大回傳 token 數 |

> 備注：`analyzer.py` 使用 `claude -p ... --model haiku` 執行分析，不直接讀取此區塊的 `model` 欄位。

### 3.3 `insights` 區塊

| 欄位 | 預設值 | 說明 |
|------|--------|------|
| `data_dir` | `"./data"` | SQLite 資料庫存放目錄（不存在時自動建立） |
| `db_name` | `"threads.db"` | SQLite 資料庫檔案名稱 |
| `backfill_days` | `30` | 回填歷史資料的天數上限（保留欄位，供未來回填功能使用） |
| `timezone` | `"Asia/Taipei"` | 報告顯示用的時區（供 report.py 格式化時間使用） |

### 3.4 `output` 區塊

| 欄位 | 預設值 | 說明 |
|------|--------|------|
| `directory` | `"./output/threads_reports"` | 日報 Markdown 檔案的輸出目錄 |

### 3.5 `${ENV_VAR}` 插值機制

`config.yaml` 支援 `${VAR_NAME}` 格式的環境變數引用。`main.load_config()` 使用正則表達式在載入 YAML 前替換所有佔位符：

```python
resolved = re.sub(r"\$\{(\w+)\}", _resolve_env, raw)
```

`_resolve_env` 從 `os.environ` 讀取對應值；若環境變數不存在，替換為空字串並印出警告訊息。

環境變數可透過以下兩種方式提供：

1. **系統環境變數**（CI/CD 或 shell `export`）
2. **`.env` 檔案**：`main._load_dotenv()` 在 `load_config` 之前讀取專案根目錄的 `.env`，以 `os.environ.setdefault` 方式載入（不覆蓋已存在的環境變數）

---

## 4. 貼文資料結構演變

一筆貼文從 Threads API 取得後，在 pipeline 各階段逐步增加欄位。

### 階段一：API 原始回傳

`threads_client._search_keyword()` 呼叫 `GET /keyword_search` 時，`fields` 參數指定回傳以下欄位：

```json
{
  "id":        "18034...",
  "text":      "GPT-4o 剛發布了新功能...",
  "username":  "techwriter_tw",
  "timestamp": "2026-03-30T12:34:56+0000",
  "like_count": 142,
  "permalink": "https://www.threads.net/@techwriter_tw/post/..."
}
```

### 階段二：`fetch_posts` 去重後（+`keyword_matched`）

`threads_client.fetch_posts()` 對每個關鍵字呼叫 API，以 `seen_ids` set 去重。第一次出現的貼文會附加 `keyword_matched` 欄位，記錄觸發此貼文的關鍵字：

```json
{
  "id":              "18034...",
  "text":            "GPT-4o 剛發布了新功能...",
  "username":        "techwriter_tw",
  "timestamp":       "2026-03-30T12:34:56+0000",
  "like_count":      142,
  "permalink":       "https://www.threads.net/@techwriter_tw/post/...",
  "keyword_matched": "GPT"
}
```

同一篇貼文符合多個關鍵字時，只保留第一個命中的關鍵字。

### 階段三：`analyze_posts` 後（+`category`、`score`、`summary`）

`analyzer.analyze_posts()` 將批次分析結果合併回每篇貼文，新增三個欄位：

```json
{
  "id":              "18034...",
  "text":            "GPT-4o 剛發布了新功能...",
  "username":        "techwriter_tw",
  "timestamp":       "2026-03-30T12:34:56+0000",
  "like_count":      142,
  "permalink":       "https://www.threads.net/@techwriter_tw/post/...",
  "keyword_matched": "GPT",
  "category":        "新工具",
  "score":           4,
  "summary":         "GPT-4o 新功能發布，多模態能力升級"
}
```

| 新增欄位 | 型別 | 可能值 |
|----------|------|--------|
| `category` | str | `新工具` / `產業動態` / `教學` / `觀點` |
| `score` | int | 1–5（AI 分析失敗時預設 2） |
| `summary` | str | 20 字以內繁體中文摘要（失敗時為固定提示文字） |

Claude 分析失敗（subprocess 錯誤或 JSON 解析失敗）時，`_fallback_analysis()` 會為該批次的所有貼文填入 `category="觀點"`、`score=2`、`summary="（AI 分析失敗，請手動查看）"`。
