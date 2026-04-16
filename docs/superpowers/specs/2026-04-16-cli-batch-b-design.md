# Spec：批次 B — Threads CLI 讀取指令 + Typer 遷移

**日期**：2026-04-16
**狀態**：Design approved，待寫 plan
**前置文件**：
- 批次 A 設計：`docs/superpowers/specs/2026-04-15-threads-cli-packaging-design.md`
- 批次 A 開發筆記：`docs/dev/batch-a-lessons.md`
- 批次 B kickoff：`docs/superpowers/handoffs/2026-04-15-batch-b-kickoff.md`

## 背景

批次 A 已完成 Threads CLI 的寫入指令（publish / reply / publish-chain），以 argparse + dispatch table 實作，全部 merge 到 main。批次 B 要加入讀取指令（6 個唯讀 + 1 個破壞性 delete），並藉此機會把整個 `threads` CLI 遷移到 Typer（因指令數將達 10+）。

## 四個議題的拍板決策

| 議題 | 決策 | 備註 |
|---|---|---|
| 1. `--json` flag | **全啟用** | 6 個新唯讀指令統一支援；統一 JSON envelope schema |
| 2. 分頁策略 | **只抓第一頁 + `--cursor`** | `posts list` / `post replies` 不自動翻頁；stderr 提示下一頁 cursor |
| 3. CLI 框架 | **同步遷移到 Typer** | 範圍翻倍接受；既有指令行為必須保留 |
| 4. Delete 保護 | **警告 + 本地備份** | `.deleted_posts/{post_id}_{timestamp}.json`；失敗策略見 Section 4 |

## Section 1：範圍

### 批次 B 涵蓋

| 項目 | 內容 |
|---|---|
| 新增唯讀指令（6） | `posts search` / `posts list` / `post insights` / `post replies` / `account info` / `account insights` |
| 新增寫入指令（1） | `post delete`（四層安全 + 本地備份 + 警告） |
| 框架遷移 | 整個 `threads` CLI（含既有 `publish` / `reply` / `publish-chain`）從 argparse 重寫到 Typer |
| `--json` 支援 | 6 個新唯讀指令全部實作 |
| 分頁策略 | `posts list` / `post replies` 只抓第一頁，支援 `--cursor` 傳入下一頁 token |

### 不動的部分（批次 A 已拍板）

- `threads-advisor` CLI 不動
- `main.py` pipeline 不動
- `publisher.py` 放 repo root
- 扁平 layout（不改 src/）
- ASCII 前綴、`--confirm --yes`、exit code 約定 0/1/2

### 預估規模

- 7 個新指令
- 3 個既有指令搬到 Typer
- 1 個 delete 獨有的備份機制
- 初估 **~18 個 task**，比批次 A 大，仍可 inline 執行

## Section 2：架構與檔案結構

### 現況

```
threads_cli/
├── cli.py           (280 行，argparse + dispatch table + 所有 handler)
├── safety.py        (四層安全)
├── output.py        (輸出 helper)
└── __init__.py
publisher.py         (repo root)
```

### 批次 B 後的目標結構

```
threads_cli/
├── __init__.py           # Typer app 宣告：app = typer.Typer()
├── main.py               # Entry point；掛載 subcommand groups
├── posts.py        (新) # posts group：search / list
├── post.py         (新) # post group：insights / replies / publish / reply /
│                         #              publish-chain / delete
├── account.py      (新) # account group：info / insights
├── safety.py             # 四層安全（沿用）
├── output.py             # 輸出 helper（擴充 --json schema）
└── _backup.py      (新) # delete 備份邏輯

publisher.py              # repo root，不動

.deleted_posts/      (新) # delete 備份目錄，.gitignore
```

### 拆檔原則

- 一個 subcommand group 一個檔
- 每個檔 ≤ 200 行
- 共用邏輯抽 helper（safety / output / _backup）
- core 邏輯仍在 `threads_pipeline/`，`threads_cli/` 只做 adapter

### 資料流（一個指令的生命週期）

```
CLI 入口 (threads posts list --limit 25 --json)
  ↓
Typer 路由 → threads_cli.posts.list_cmd()
  ↓
handler 呼叫 threads_pipeline.threads_client.list_my_posts(limit=25)
  ↓
core 回 dict {"posts": [...], "next_cursor": "..."}
  ↓
output.py 判斷 --json
    ├── --json → json.dumps 到 stdout
    └── 人類模式 → 格式化文字表格到 stdout
錯誤 → stderr（ASCII 前綴）+ exit code（0/1/2）
```

## Section 3：指令規格

### 7 個新指令的 signature

| 指令 | 主要參數 / flag | 備註 |
|---|---|---|
| `threads posts search <kw>` | `--limit N` (預設 25) / `--json` | 中文/跨帳號受 Standard Access 限制 |
| `threads posts list` | `--limit N` / `--cursor TOKEN` / `--json` | 列自己貼文，支援分頁 |
| `threads post insights <id>` | `--json` | views/likes/replies/reposts 等 |
| `threads post replies <id>` | `--limit N` / `--cursor TOKEN` / `--json` | 同 list 分頁模式 |
| `threads account info` | `--json` | id/username/biography 等 |
| `threads account insights` | `--json` | followers/views 等帳號級數據 |
| `threads post delete <id>` | `--confirm` / `--yes` / `--json` | 四層安全 + 備份 |

### 統一的 JSON envelope

所有唯讀指令共用同一個 schema：

```json
// 成功
{"ok": true, "data": {...}}

// 分頁（list / replies）
{"ok": true, "data": {...}, "next_cursor": "QVFIUkR..."}

// 失敗
{"ok": false, "error": {"code": "TOKEN_MISSING", "message": "..."}}
```

### 分頁的 stderr 提示（人類模式）

`list` / `replies` 若還有下一頁，stderr 印：

```
[INFO] 還有更多資料。下一頁請加：--cursor QVFIUkR...
```

stdout 只放資料、stderr 放提示——符合批次 A 的 stdout/stderr 分流原則。

### `threads post delete` 的完整流程

```
threads post delete <post_id>
  → [dry-run] 顯示要刪的內容預覽 + 警告
  → 提示：要真刪請加 --confirm --yes

threads post delete <post_id> --confirm --yes
  → (1) GET /{post_id} 抓完整內容
  → (2) 寫 .deleted_posts/{post_id}_{YYYYMMDD-HHMMSS}.json
  → (3) DELETE /{post_id}
  → (4) 成功：stdout 印備份路徑 + 「此操作不可逆」警告
  → (4) 失敗：備份保留、exit code 1、stderr 報錯
```

**失敗 case 的處理**（exit code 皆為 1，屬執行失敗類別）：
- 備份寫失敗 → **不執行 DELETE**（exit code 1、error code `BACKUP_FAILED`）
- DELETE 失敗但備份成功 → 備份保留供下次重試（exit code 1、error code `DELETE_FAILED`）

### 既有指令遷移到 Typer 的行為保留契約

**遷移後必須與批次 A 完全一致**：
- Positional 參數順序不變（`threads post publish "文字"` 不變）
- Flag 名稱不變（`--confirm` / `--yes` / `--dry-run`）
- Exit code 不變（0/1/2）
- Stderr 訊息格式不變（`[ERROR]` / `[OK]` 前綴）
- `publish-chain` 吃 `drafts/*.txt` 的行為不變
- **`publish-chain` 的 rollback 不做**：批次 A spec 提過可依賴 `post delete` 實作串文發布過程中的 rollback，批次 B **不實作此功能**（維持批次 A 行為，發布過程中出錯仍需手動 delete）。Rollback 功能若需要留到批次 C 評估。

**驗證方式**：批次 A smoke 的每一步都必須可以重跑、輸出一致。寫一個專門的「遷移驗證 task」對照跑。

## Section 4：測試策略、錯誤處理、驗收標準

### 測試分層

| 層 | 範圍 | 工具 | 絕對不做 |
|---|---|---|---|
| Unit | 每個 command handler 的邏輯 | mock `requests` / `threads_client` | **絕不**打真 API |
| Integration | Typer app CLI 呼叫→parse→dispatch→output | `typer.testing.CliRunner` | — |
| Smoke（手動） | 真打 Threads API | 終端機手動 | 自動 CI 跑（會扣 rate limit） |

### 遷移驗證（Typer 遷移獨有）

三層保護：

1. **既有 87 tests 全綠**：Typer 版本跑完後所有既有測試必須通過，不能改測試配合新實作
2. **行為對照表**：挑 10 個關鍵 case（flag 組合、error path、exit code、stderr 格式）列表格，argparse 輸出 vs Typer 輸出必須逐字一致（除了框架自動生成的 help 文字）
3. **批次 A smoke 重跑**：`docs/superpowers/handoffs/2026-04-15-threads-cli-smoke.md` 的每一步重跑一次，結果與批次 A 一致

### Exit code 約定（沿用批次 A）

- `0`：成功
- `1`：執行失敗（API error、network、unexpected）
- `2`：使用者錯誤（缺 token、flag 組合錯、post_id 格式錯）

### Error code（`--json` 模式專用）

| Code | 適用 |
|---|---|
| `TOKEN_MISSING` | .env 沒載或 token 空 |
| `API_ERROR` | Threads API 5xx / 4xx（含 HTTP status 在 message 裡） |
| `RATE_LIMIT` | 429 |
| `NOT_FOUND` | post_id 不存在 |
| `INVALID_ARGS` | 參數/旗標錯 |
| `BACKUP_FAILED` | delete 備份寫入失敗（**不往下執行 DELETE**） |
| `DELETE_FAILED` | DELETE 請求本身失敗（**備份保留**） |

### 驗收標準（批次 B 何時算完成）

- [ ] 7 個新指令全部實作 + unit test 綠
- [ ] 既有 87 tests 全綠（Typer 遷移後）
- [ ] Typer integration test：每個指令至少 1 個 CliRunner case
- [ ] 行為對照表 10 個 case 全 pass
- [ ] 手動 smoke：6 唯讀指令各跑一次（`--json` 兩種模式）、delete 真跑一次 + 驗備份檔、publish/reply/publish-chain 回歸
- [ ] `.deleted_posts/` 加入 `.gitignore`
- [ ] `typer` 依賴加到 `pyproject.toml`
- [ ] Smoke handoff：寫 `docs/superpowers/handoffs/2026-04-XX-batch-b-smoke.md`

### 風險紅旗（要在 plan 層處理）

- Typer 有些 edge case 跟 argparse 行為不同（例如 `--flag=value` vs `--flag value`），要在遷移 task 裡事先列清楚
- Delete 的備份目錄若不存在要自動建（handler 職責，不是前置條件）
- `posts search` 中文 Standard Access 限制要寫入 `--help` 文字，不是隱性行為

## 開放項待 plan 階段決定

- 18 個 task 的具體切割與順序（遷移先做 vs 新指令先做）
- 每個 task 的 commit 邊界
- 雙審查（spec reviewer + plan reviewer）由哪個 agent 執行
- 新分支名稱：建議 `feat/cli-batch-b`

## 不在範圍內（Out of scope）

- 跨帳號搜尋（Advanced Access 未核准前功能受限）
- delete 的 undo to Threads（技術上不可能）
- CLI 框架從 Typer 再換到別的（已拍板 Typer）
- `threads-advisor` CLI 改動
- `main.py` pipeline 改動
