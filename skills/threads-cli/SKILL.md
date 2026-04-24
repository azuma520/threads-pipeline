---
name: threads-cli
description: "How to use the `threads` CLI and `threads-advisor` tools to operate the user's Threads account — publish posts, reply, list/search posts, fetch insights, delete posts, analyze performance, review drafts. Use this skill whenever the user asks to post on Threads, check their Threads analytics/insights, list or search their posts, reply to a post, delete a post, analyze which posts perform best, review a draft before posting, or any Threads account operation. Also use when the user mentions 'threads' CLI, 'advisor', Threads API operations, content strategy, or wants to interact with their Meta Threads account programmatically."
---

# Threads CLI — Agent 操作手冊

兩套工具搭配使用：
- **`threads`** — 直接操作 Threads 帳號（發文、查資料、刪文）
- **`threads-advisor`** — AI 顧問（分析數據、審查草稿）

所有寫入指令預設 dry-run（不會真的執行），加 `--confirm --yes` 才會真跑。

## 前置條件

- 環境變數 `THREADS_ACCESS_TOKEN` 必須已設（通常在 `.env`）
- CLI 入口：`threads` / `threads-advisor`（透過 `pip install -e .` 安裝）

## 指令總覽

### threads（帳號操作）

| 指令 | 用途 | 寫入？ | `--json` |
|------|------|--------|----------|
| `threads account info` | 帳號基本資料 | 否 | 有 |
| `threads account insights` | 帳號數據（views/likes/followers） | 否 | 有 |
| `threads posts list` | 列出自己的貼文（分頁） | 否 | 有 |
| `threads posts search "keyword"` | 搜尋貼文 | 否 | 有 |
| `threads post insights <post_id>` | 單篇貼文數據 | 否 | 有 |
| `threads post replies <post_id>` | 單篇貼文的回覆 | 否 | 有 |
| `threads post publish "text"` | 發文 | 是 | 否 |
| `threads post publish-chain file` | 發串文 | 是 | 否 |
| `threads reply add <post_id> "text"` | 回覆貼文 | 是 | 否 |
| `threads reply hide <reply_id>` | 隱藏某則回覆 | 是 | 否 |
| `threads reply unhide <reply_id>` | 取消隱藏某則回覆 | 是 | 否 |
| `threads account mentions` | 查看 @mentions（我被提及的貼文） | 否 | 有 |
| `threads profile lookup <URL>` | URL → 讀他人公開貼文 text（學習用）⚠️ 需 `profile_discovery` 核准 | 否 | 有 |
| `threads profile posts <username>` | 列某帳號公開貼文 ⚠️ 需 `profile_discovery` 核准 | 否 | 有 |
| `threads post delete <post_id>` | 刪除貼文 | 是 | 有 |

### threads-advisor（AI 顧問）

| 指令 | 用途 |
|------|------|
| `threads-advisor analyze` | 從 SQLite 資料庫產生帳號分析報告（top posts + 趨勢），用 Claude AI 分析 |
| `threads-advisor analyze --date 2026-04-17` | 指定日期的分析 |
| `threads-advisor review drafts/my-post.txt` | AI 審查草稿檔案，給出發文建議 |
| `threads-advisor review --text "草稿文字"` | 直接審查文字 |
| `threads-advisor review --plan plan.md` | 搭配 plan 檔審查 |

## 什麼時候用哪個工具

| 使用者想要 | 用這個 | 原因 |
|-----------|--------|------|
| 查即時數據（現在有幾個讚） | `threads post insights` | 直接打 API 拿最新數字 |
| 看整體趨勢（最近哪篇最好） | `threads-advisor analyze` | 從 SQLite 撈歷史數據 + AI 分析 |
| 發文前審查草稿 | `threads-advisor review` | AI 給出文案建議 |
| 發文 / 回覆 / 刪文 | `threads post ...` / `threads reply` | 直接操作 API |
| 列出自己所有文 | `threads posts list` | API 查詢，支援分頁 |
| 搜尋特定關鍵字的文 | `threads posts search` | API 搜尋（限制多，見下方） |

## JSON Envelope 格式

加 `--json` flag 的指令回傳統一的 JSON envelope，方便程式解析：

成功：
```json
{"ok": true, "data": {...}, "warnings": [...], "next_cursor": "..."}
```

失敗：
```json
{"ok": false, "error": {"code": "ERROR_CODE", "message": "..."}}
```

常見 error code：`API_ERROR`、`NOT_FOUND`、`RATE_LIMIT`、`BACKUP_FAILED`、`DELETE_FAILED`

## 唯讀指令

### 查帳號

```bash
# 帳號資料（username / bio / 大頭照）
threads account info --json

# 帳號數據（views / likes / replies / followers_count）
threads account insights --json
```

### 列出 / 搜尋貼文

```bash
# 列出最近貼文（預設 25 篇）
threads posts list --limit 10 --json

# 翻頁：用上一次回傳的 next_cursor
threads posts list --cursor "QVFI..." --json

# 搜尋（Standard Access 限制：只搜得到自己的文、中文關鍵字通常回 0 筆）
threads posts search "AI" --json
```

### 單篇貼文

```bash
# 貼文數據（views / likes / replies / reposts / quotes）
threads post insights <post_id> --json

# 貼文回覆列表（支援 --cursor 翻頁）
threads post replies <post_id> --limit 10 --json
```

## 寫入指令

寫入指令預設 dry-run。加 `--confirm --yes` 才會真的執行（Agent 模式）。

### 發文

```bash
# dry-run（預覽，不會真發）
threads post publish "你的文字"

# 真發
threads post publish "你的文字" --confirm --yes
```

### 串文

```bash
# 檔案中每一行是一則貼文
threads post publish-chain drafts/my-thread.txt --confirm --yes
```

### 回覆

```bash
# 新增回覆
threads reply add <post_id> "回覆內容" --confirm --yes

# 隱藏 / 取消隱藏他人的回覆（reply_id 從 threads post replies 取得）
threads reply hide <reply_id>
threads reply unhide <reply_id>
```

### 刪除

刪除有四層安全防護：token → `--confirm --yes` → 互動確認（TTY）→ 備份後才刪。

```bash
# dry-run（預覽）
threads post delete <post_id>

# dry-run + JSON envelope
threads post delete <post_id> --json

# 真刪（會先備份到 .deleted_posts/）
threads post delete <post_id> --confirm --yes
```

## 常見工作流

### 「我想看哪篇文表現最好」

**快速版**（有跑過 pipeline、SQLite 有資料）：
```bash
threads-advisor analyze
```
一行搞定——從 SQLite 撈 top posts + 帳號趨勢，Claude AI 產出分析報告。

**手動版**（即時資料、不依賴 SQLite）：
1. `threads posts list --limit 20 --json` → 拿到貼文 ID 列表
2. 對每篇跑 `threads post insights <id> --json` → 比較 views / likes
3. 整理成排行報告

### 「我想了解帳號整體狀況」

```bash
# 一次看基本資料 + 數據
threads account info --json
threads account insights --json
threads posts list --limit 5 --json
```

如果要更深入的 AI 分析：
```bash
threads-advisor analyze
```

### 「幫我發一篇文再確認有沒有成功」

1. `threads post publish "文字" --confirm --yes` → 取得 post_id
2. `threads post insights <post_id> --json` → 確認數據開始累積

### 「幫我審查這篇草稿再發出去」

1. `threads-advisor review --text "草稿文字"` → AI 審查，給建議
2. 根據建議修改
3. `threads post publish "修改後的文字" --confirm --yes` → 發文

如果草稿是檔案：
1. `threads-advisor review drafts/my-post.txt` → AI 審查
2. 修改檔案內容
3. `threads post publish-chain drafts/my-post.txt --confirm --yes`（串文）或複製內容用 `post publish`

### 「我想刪掉某篇文」

1. `threads post insights <post_id> --json` → 先確認是哪篇
2. `threads post delete <post_id>` → dry-run 預覽
3. 確認後 `threads post delete <post_id> --confirm --yes`
4. 備份在 `.deleted_posts/` 目錄

### 「我想回覆某篇文的留言」

1. `threads post replies <post_id> --json` → 看有哪些回覆
2. 找到要回覆的 reply_id
3. `threads reply add <reply_id> "回覆內容" --confirm --yes`

### 「我想發串文」

1. 準備檔案（每行一則貼文）：`drafts/my-thread.txt`
2. `threads-advisor review drafts/my-thread.txt` → AI 審查每則內容
3. `threads post publish-chain drafts/my-thread.txt` → dry-run 預覽
4. `threads post publish-chain drafts/my-thread.txt --confirm --yes` → 真發

### 「每天早上跑一次完整 pipeline」

```bash
PYTHONUTF8=1 python -m threads_pipeline.main
```
這會跑 Job A（趨勢收集 + AI 分析）和 Job B（insights 追蹤 + 戰情日報），報告存在 `output/threads_reports/`。跑完後 `threads-advisor analyze` 就能撈到最新資料。

## 注意事項

- `--yes` 不能單獨用，一定要搭配 `--confirm`，否則 exit 2
- `posts search` 在 Standard Access 下只搜得到自己的文，中文關鍵字通常回 0 筆
- 分頁指令有 `next_cursor` 時代表還有下一頁，用 `--cursor` 繼續
- 刪除是不可逆的，備份檔在 `.deleted_posts/{post_id}_{timestamp}.json`
- `threads-advisor analyze` 需要 SQLite 有資料（先跑過 `python -m threads_pipeline.main`）
- 所有輸出使用繁體中文
