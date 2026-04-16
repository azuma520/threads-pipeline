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

### 預估規模與切段策略

批次 B 切成兩個獨立段（**B1 先、B2 後**），各自有獨立 commit series、可獨立驗證 merge：

**B1 — Typer 遷移 + 既有指令回歸**
- `typer` 依賴加入 `pyproject.toml`
- `threads_cli/` 重構：拆成 `posts.py` / `post.py` / `account.py` / `main.py` 骨架
- 既有 3 指令（`publish` / `reply` / `publish-chain`）遷移到 Typer
- Subprocess 黑箱測試層建立（見 Section 4）+ 既有 87 tests 重寫
- 批次 A smoke 重跑全綠才算 B1 結案

**B2 — 新增 7 指令 + delete 備份**
- 6 唯讀指令（`posts search / list`、`post insights / replies`、`account info / insights`）
- `post delete` + `.deleted_posts/` 備份機制
- 新指令 unit + integration test、各自 smoke

初估 task 數：B1 ~8 task、B2 ~10 task。**B1 卡住不會 block B2 新指令實作規劃**（只是上線順序仍 B1 先）。

### 為什麼切兩段

- Typer 遷移風險高（regression 潛在點多），獨立一段可單獨回滾
- B1 結束後有明確 milestone：「既有指令全部跑過 Typer + subprocess 黑箱測試」，才開始加新功能
- 若 B1 結束發現 Typer 有意外 blocker，至少不會拖累新指令實作

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
                         # ⚠ 本 repo 位於 OneDrive 路徑下，備份會被自動同步至雲端。
                         # 若介意，請在 OneDrive 設定「排除此資料夾」。
                         # 備份內容為自己發的貼文，本專案評估風險可接受。
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
| `threads posts search <kw>` | `--limit N` (預設 25) / `--json` | Standard Access 限制——見下方 search 專屬說明 |
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

// 成功 + 警告（例：中文 Standard Access 回 0、limit clamp 到 25）
{"ok": true, "data": {...}, "warnings": [
  {"code": "EMPTY_RESULT_CJK", "message": "Standard Access 下中文搜尋常回 0 筆"},
  {"code": "LIMIT_CLAMPED", "message": "limit 從 100 clamp 到 25（API 上限）"}
]}

// 分頁（list / replies）
{"ok": true, "data": {...}, "next_cursor": "QVFIUkR..."}

// 失敗
{"ok": false, "error": {"code": "TOKEN_MISSING", "message": "..."}}
```

**警告通道規則**：
- `warnings` 為陣列，空或不存在都代表無警告（呼叫者 `.get("warnings", [])` 即可）
- 警告**同步**走 stderr 的 `[WARN]` 前綴訊息（人類也看得到）
- JSON mode 下 stdout 只有一行 JSON（envelope），warnings 包在 envelope 內，stderr 仍有人類可讀版
- `warnings` 不影響 `ok: true`（成功但有提示，不是失敗）

### `posts search` 的特殊處理（Standard Access 限制）

Spec 保留此指令實作，但必須明示受限狀態：

- **`--help` 頂端大字警告**：明示 Standard Access 下「只能搜自己的貼文、中文關鍵字通常回 0 筆」，Advanced Access 核准後才可跨帳號/中文有效
- **偵測中文關鍵字**：指令執行時若 keyword 含 CJK 字元，stderr 先印 `[WARN] 中文搜尋在 Standard Access 下通常回 0 筆，建議改用 threads posts list`；JSON 模式加 `EMPTY_RESULT_CJK` 警告到 envelope
- **結果為 0 筆時**：stderr 提示「若本應有結果，可能是 Standard Access 限制」，不視為 error（exit code 0）

### 分頁的 stderr 提示（人類模式）

`list` / `replies` 若還有下一頁，stderr 印：

```
[INFO] 還有更多資料。下一頁請加：--cursor QVFIUkR...
```

stdout 只放資料、stderr 放提示——符合批次 A 的 stdout/stderr 分流原則。

### `threads post delete` 的完整流程

```
threads post delete <post_id>
  → [dry-run] **不呼叫任何 API**（零副作用、不吃 rate limit）
  → stdout 印「DRY RUN: will delete post_id=<id>」
  → stderr 印「此操作不可逆。要真刪請加 --confirm --yes」
  → 要看內容請先用 threads post insights <id> 或 threads post replies <id>
  → exit code 0

threads post delete <post_id> --confirm --yes
  → (1) GET /{post_id} 抓完整內容（欄位含 text、media、timestamp、permalink）
  → (2) 寫 .deleted_posts/{post_id}_{YYYYMMDD-HHMMSS}.json
        備份 JSON 含 metadata：captured_at（ISO 時間戳）、captured_before_delete: true
  → (3) DELETE /{post_id}
  → (4) 成功：stdout 印備份路徑 + 「此操作不可逆」警告
  → (4) 失敗：備份保留、exit code 1、stderr 報錯
```

**為什麼 dry-run 不做 GET**：讓 dry-run 保持真正零副作用（不吃 rate limit、不會因 404 失敗），符合使用者對 `--dry-run` 的直覺。若要預覽內容，使用者/Agent 可先呼叫 `post insights` 或 `post replies` 等唯讀指令。

**備份是「DELETE 前快照」**：GET 和 DELETE 之間有微小時間差（<1 秒），若期間使用者在 Threads app 內改動，備份可能不等於刪除瞬間內容。`captured_at` 欄位讓使用者能辨認快照時點。

**失敗 case 的處理**（exit code 皆為 1，屬執行失敗類別）：
- 備份寫失敗 → **不執行 DELETE**（exit code 1、error code `BACKUP_FAILED`）
- DELETE 失敗但備份成功 → 備份保留供下次重試（exit code 1、error code `DELETE_FAILED`）

### 既有指令遷移到 Typer 的行為保留契約

**遷移後必須一致的部分（可自動化驗證）**：
- Positional 參數順序不變（`threads post publish "文字"` 不變）
- Flag 名稱不變（`--confirm` / `--yes` / `--dry-run`）
- Exit code 不變（0/1/2）
- **我方輸出**的 ASCII 前綴不變（`[ERROR]` / `[OK]` / `[INFO]` / `[WARN]`）
- `publish-chain` 吃 `drafts/*.txt` 的行為不變

**允許改變的部分（Typer/Click 底層控制，無法逐字保留）**：
- `--help` 排版（argparse 的 `usage:` vs Click 的 `Usage:`）
- 框架自動產生的 error 訊息（argparse 的 `error: the following arguments are required: text` vs Click 的 `Error: Missing argument 'TEXT'.`）——exit code 仍是 2、但訊息文字不同
- argparse 的 prog name 行為與 Click 不完全一致

**不做的（明確 scope out）**：
- **`publish-chain` 的 rollback 不做**：批次 A spec 提過可依賴 `post delete` 實作串文發布過程中的 rollback，批次 B **不實作此功能**（維持批次 A 行為，發布過程中出錯仍需手動 delete）。Rollback 功能若需要留到批次 C 評估。

**驗證方式**：見 Section 4「遷移驗證」——subprocess 黑箱測試只驗 exit code + ASCII 前綴 + 我方輸出語意，不驗框架內建訊息逐字。

## Section 4：測試策略、錯誤處理、驗收標準

### 測試分層

| 層 | 範圍 | 工具 | 絕對不做 |
|---|---|---|---|
| Unit | 每個 command handler 的邏輯 | mock `requests` / `threads_client` | **絕不**打真 API |
| Integration | Typer app 內部 parse→dispatch→output | `typer.testing.CliRunner` | — |
| **Subprocess 黑箱**（新增） | 從 shell 真跑 `threads` 指令，斷言 exit code + stdout/stderr 語意 | `subprocess.run(["threads", ...])` | 打真 API（用 mock Token + 可離線斷言的 path） |
| Smoke（手動） | 真打 Threads API | 終端機手動 | 自動 CI 跑（會扣 rate limit） |

### 遷移驗證（Typer 遷移獨有，B1 段執行）

**關鍵認知**：既有 87 tests 大多 mock argparse namespace 直接呼叫 `cmd_*(args)`，Typer 遷移後 handler signature 改變，**這些 test 必須重寫**。若只盯著「87 tests 綠」會變成假安全感——因為測試本身已被修改。

三層保護：

1. **Subprocess 黑箱測試（遷移前先建）**
   - 對**既有 3 個指令**（publish / reply / publish-chain）+ 關鍵 error path 寫 10-15 個 subprocess case
   - 斷言：exit code、stdout 是否含 `[OK]`、stderr 是否含 `[ERROR]`/`[WARN]`/`[INFO]` 前綴與預期 payload
   - **不**斷言框架自動訊息（`Error: Missing argument ...`）逐字
   - 這層**在 argparse 時代就寫好、跑過綠**，遷移 Typer 後**不改這層**，必須仍全綠——這才是真正的 regression 防線
2. **重寫既有 87 tests 配合 Typer handler signature**（預期的、不是問題）
3. **批次 A smoke 重跑**：`docs/superpowers/handoffs/2026-04-15-threads-cli-smoke.md` 的每一步重跑一次，結果與批次 A 一致

### B1 / B2 驗收切點

- **B1 結案條件**：subprocess 黑箱測試全綠 + 重寫後 87 tests 全綠 + 批次 A smoke 重跑通過
- **B2 結案條件**：新指令 unit + integration + subprocess 黑箱（各新指令至少 1 case）+ 手動 smoke 全跑

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

**B1（Typer 遷移段）**：

- [ ] `typer` 依賴加到 `pyproject.toml`
- [ ] **Subprocess 黑箱測試 10-15 case 建立並全綠**（argparse 時代先做、遷移後不動必須仍全綠）
- [ ] 既有 87 tests 重寫配合 Typer handler signature，全綠
- [ ] Typer integration test：既有 3 指令各至少 1 個 CliRunner case
- [ ] 批次 A smoke handoff 每一步重跑通過
- [ ] B1 commit series merge 到 main

**B2（新指令 + delete 段）**：

- [ ] 7 個新指令全部實作 + unit test 綠
- [ ] Typer integration test：新指令各至少 1 個 CliRunner case
- [ ] Subprocess 黑箱測試：新指令各至少 1 case
- [ ] 手動 smoke：6 唯讀指令各跑一次（`--json` 兩種模式）、delete 真跑一次 + 驗備份檔
- [ ] `.deleted_posts/` 加入 `.gitignore`
- [ ] Smoke handoff：寫 `docs/superpowers/handoffs/2026-04-XX-batch-b-smoke.md`（`2026-04-XX` 於實際執行日填入）

### 風險紅旗（要在 plan 層處理）

- Typer 有些 edge case 跟 argparse 行為不同（例如 `--flag=value` vs `--flag value`），要在遷移 task 裡事先列清楚
- Delete 的備份目錄若不存在要自動建（handler 職責，不是前置條件）
- `posts search` 中文 Standard Access 限制要寫入 `--help` 文字，不是隱性行為

## 開放項待 plan 階段決定

- B1（~8 task）與 B2（~10 task）的具體 task 切割、順序與 commit 邊界
- 分支策略：建議 B1 走 `feat/cli-batch-b1`、merge 後再開 `feat/cli-batch-b2`
- subprocess 黑箱測試的詳細 10-15 個 case 列表
- 雙審查（spec reviewer + plan reviewer）由哪個 agent 執行
- `--limit` 各指令的 default / max / 超限 clamp 行為（spec 已定政策，具體數值 plan 補）
- Typer `--json` 全域 flag 的實作方式（root callback + `ctx.obj` vs 每個 command 各自宣告）
- 備份檔 metadata schema 細節（`captured_at` 格式、其他欄位）
- `.deleted_posts/` 建失敗時的 exit code 與 error code 歸類（預設 `BACKUP_FAILED`）

## 不在範圍內（Out of scope）

- 跨帳號搜尋（Advanced Access 未核准前功能受限）
- delete 的 undo to Threads（技術上不可能）
- CLI 框架從 Typer 再換到別的（已拍板 Typer）
- `threads-advisor` CLI 改動
- `main.py` pipeline 改動
