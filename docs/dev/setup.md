# 開發環境設置

## 1. 系統需求

| 項目 | 需求 |
|------|------|
| Python | 3.13 以上 |
| Claude Code CLI | `claude` 指令需可用（analyzer 使用 `claude -p`） |
| 作業系統 | Windows 11（開發環境） |

Claude Code CLI 安裝請參考官方文件。確認可用的方式：

```bash
claude --version
```

---

## 2. 依賴安裝

```bash
pip install requests pyyaml jinja2
```

專案不使用 `requirements.txt`，以上三個套件即為完整依賴。

---

## 3. Threads API Token 設定

### 申請方式

需要 Meta Threads API **Standard Access**（非 Basic Access）。申請入口為 Meta for Developers，需完成 App Review。

### 存取範圍限制

Standard Access 只能讀取**自己帳號**的貼文和 insights，無法搜尋或讀取其他帳號的內容。

### Token 有效期

- Long-lived token 有效期為 **60 天**
- 到期前請使用 refresh endpoint 換發新 token

```
GET https://graph.threads.net/refresh_access_token
    ?grant_type=th_refresh_token
    &access_token=<現有 token>
```

### Token 過期的後果

Token 過期後 API 會回傳 HTTP 403。`main.py` 的每個 Job 都有獨立的 `try/except`，過期不會拋出例外中斷程式，而是靜默失敗——console 只會顯示 `✗ 成效追蹤失敗` 之類的訊息。

定期確認 token 有效期，避免資料缺漏。

---

## 4. .env 設定

在專案根目錄建立 `.env` 檔案：

```
THREADS_ACCESS_TOKEN=你的token
```

`.gitignore` 已將 `.env` 排除，不會被提交。

`main.py` 在執行主流程前會呼叫 `_load_dotenv()`，讀取此檔案並以 `os.environ.setdefault` 載入（不覆蓋已存在的環境變數）。

`config.yaml` 中 `threads.access_token` 欄位使用 `${THREADS_ACCESS_TOKEN}` 語法，由 `load_config()` 在讀取時解析替換。

---

## 5. 執行方式

```bash
PYTHONUTF8=1 python -m threads_pipeline.main
```

`PYTHONUTF8=1` 是 Windows 上必要的設定，確保中文輸出正常。`main.py` 頂層也有 `os.environ.setdefault("PYTHONUTF8", "1")`，但直接在指令前設定是更可靠的做法，避免 import 時就出現 encoding 問題。

---

## 6. 部署排程

### Linux / macOS（cron）

每天 UTC 00:00 執行（台灣時間 08:00）：

```bash
0 0 * * * cd /path/to/threads_pipeline && PYTHONUTF8=1 python -m threads_pipeline.main >> logs/pipeline.log 2>&1
```

記得先建立 `logs/` 目錄：

```bash
mkdir -p logs
```

### Windows（Task Scheduler）

Windows 上使用「工作排程器」（Task Scheduler）替代 cron：

1. 開啟「工作排程器」
2. 建立基本工作，觸發條件設定為每日指定時間
3. 動作選「啟動程式」，程式填 `python`，引數填 `-m threads_pipeline.main`
4. 起始位置填專案根目錄路徑
5. 在「設定」確認有 `PYTHONUTF8=1` 的環境變數，或改用 `.bat` 包裝

範例 `.bat`：

```bat
@echo off
set PYTHONUTF8=1
cd /d C:\path\to\threads_pipeline
python -m threads_pipeline.main >> logs\pipeline.log 2>&1
```
