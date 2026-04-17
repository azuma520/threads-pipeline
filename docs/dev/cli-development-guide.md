# CLI 工具開發指南（Agent-Driven）

從 threads CLI 的 B1→B2→B3 開發經驗整理而成。適用於：用 Agent 開發、給 Agent 使用的 CLI 工具。

## 架構

### 先定 Envelope，再寫指令

第一個 commit 就是 envelope schema + helpers，不要讓各指令各自發明輸出格式。

```json
{"ok": true, "data": ..., "warnings": [...], "next_cursor": "..."}
{"ok": false, "error": {"code": "...", "message": "..."}}
```

`warnings` 陣列讓 Agent 知道「成功了但有注意事項」，不用 parse stderr。`next_cursor` 統一分頁協議。

### 三層檔案結構

```
cli/
├── cli.py          # 入口 + global flags + error handling
├── output.py       # 所有輸出格式化（envelope / error / warn）
├── safety.py       # token / confirm / yes 安全層
├── <domain>.py     # 各領域指令（一個檔案一個 Typer sub-app）
└── _<internal>.py  # 內部模組（如 _backup.py）
```

`output.py` 和 `safety.py` 是橫切面，所有指令共用。domain 檔案不直接 `print()` 或 `sys.exit()`——一律透過 `emit_envelope_json()` / `error_with_code()` / `warn_with_code()`。

### Core helpers 和 CLI handlers 分離

```
api_client.py       ← 純 API 封裝，回傳 dict，raise exception
cli/<domain>.py     ← 拿 dict，轉成 envelope / 人讀格式
```

不要在 core helper 裡做 CLI 的事（print / exit），不要在 CLI handler 裡做 HTTP 請求。好處：
- Core helper 可被多個入口共用（CLI / pipeline / SDK）
- CLI handler 的測試用 mock 就夠，不需要真打 API
- 替換 API（例如改用 SDK）只改 core，CLI 層不動

### Global `--json` flag 的傳遞

兩種方式：

**方式 A（推薦）**：每個指令自帶 `--json` option，直接在 handler 裡用。簡單直接，但重複。

**方式 B**：root callback 定義一次，透過 Typer Context 傳遞。更 DRY，但需要理解 Click Context 機制。

不要用 `sys.argv` 解析——那是 workaround，不是設計。

## 代碼模式

### Handler 統一模板

每個指令都應該長這樣：

```python
@app.command("xxx")
def xxx_cmd(
    # args / options
    json_mode: bool = typer.Option(False, "--json", help="..."),
):
    token = require_token(json_mode=json_mode)
    try:
        data = core_helper(token, ...)
    except requests.exceptions.RequestException as e:
        error_with_code(code, msg, json_mode=json_mode)

    if json_mode:
        emit_envelope_json(data, warnings=warnings, next_cursor=next_cursor)
        return

    # 人類模式
    print(...)
```

每個新指令只需改三個地方：core helper 呼叫、error mapping、人類模式輸出。Plan 裡把模板寫清楚，implementer agent 幾乎不會出錯。

### Error code 體系

一開始就定義 error code 表，不要事後補：

| Code | 意義 | 觸發場景 |
|------|------|---------|
| `TOKEN_MISSING` | 環境問題 | 缺 access token |
| `INVALID_ARGS` | 使用者輸入錯 | Typer 框架層攔截 |
| `API_ERROR` | 通用 API 失敗 | 非特定 HTTP error |
| `NOT_FOUND` | 資源不存在 | 404 |
| `RATE_LIMIT` | 被限速 | 429 |
| `BACKUP_FAILED` | 本地 IO 問題 | 備份寫入失敗 |

Agent 讀到 `NOT_FOUND` 就知道「資源不存在」，不用 parse message 字串。error code 比人讀的 error message 重要得多。

### Dry-run / Confirm / Yes 三層安全

任何破壞性操作（publish / delete / reply）都套這個模式：

```python
# 預設 dry-run
if not confirm:
    print("[DRY RUN] Would ...")
    return

# 非 TTY 必須 --yes
validate_confirm_yes(confirm=confirm, yes=yes, is_tty=is_tty)

# TTY 互動確認
if not yes:
    if not interactive_confirm("Really do this?"):
        print("(cancelled)")
        return

# 真正執行
```

Agent 預設就是非 TTY 環境，`--confirm --yes` 是 Agent 「有意識地」選擇執行的信號。Dry-run 讓人類在 Agent 的計畫裡看到 flag 組合，決定要不要放行。

### 分頁協議

統一用 `--cursor` + `--limit`，回傳 `next_cursor`：

```python
def list_xxx(token, limit=25, cursor=None) -> dict:
    # ...
    return {"items": [...], "next_cursor": "..." or None}
```

人類模式加 `[INFO] 還有更多資料。下一頁請加：--cursor XXX` 提示。Agent 看 `next_cursor` 有值就知道要翻頁。

## 測試策略

### 三層測試金字塔

| 層 | 測什麼 | 工具 | 數量 |
|---|---|---|---|
| Unit | Core helpers（mock HTTP） | pytest + mock | 多 |
| CliRunner | Handler 邏輯（mock core helpers） | typer.testing.CliRunner | 多 |
| Subprocess 黑箱 | 真跑 CLI binary，驗 exit code + 輸出片段 | subprocess.run | 少但關鍵 |

黑箱測試是最重要的防線——CliRunner 有時候隱藏 Typer/Click 的行為差異（例如 `mix_stderr` 輸出順序），subprocess 黑箱從使用者角度驗證。Agent 實際用的就是 subprocess。

### Mock target 要 patch「使用的地方」

```python
# 錯：patch 定義的地方
patch("my_project.api_client.fetch_data")

# 對：patch import 進來的地方
patch("my_project.cli.account.fetch_data")
```

在 Plan 裡一定要寫清楚 mock target path。Implementer agent 最常犯的就是 patch 錯位置——測試會過但沒有真的 mock 到。

### 測試檔案的命名慣例

```
test_cli_<domain>.py         → 某個子指令群
test_cli_<specific>.py       → 複雜指令獨立測試（如 delete）
test_cli_<crosscutting>.py   → 橫切面測試（如 token_missing）
test_cli_blackbox.py         → 全部黑箱測試集中
test_<core>_<scope>.py       → core helpers
test_output_*.py             → 輸出層
```

一個檔案對一個關注點。Agent 開新指令時，知道要在哪個檔案加測試。

### CliRunner 的 JSON 提取

Python 3.13 + Typer 的 CliRunner 預設 `mix_stderr=True`，stdout 在前、stderr 在後。提取 JSON 用：

```python
start = result.output.find("{")
end = result.output.rfind("}") + 1
parsed = json.loads(result.output[start:end])
```

不要假設 JSON 在第一行或最後一行。

## Plan 撰寫

### 不能有 placeholder

```
# 錯
"加入適當的 error handling"
"類似 Task 3 的做法"

# 對
完整的 code block，包含 import / function body / test assertion
```

Implementer agent 是全新的，看不到其他 task 的結果。每個 task 必須自包含。

### Import 修改要獨立步驟

Plan 裡的 handler 新增應該拆成：
- Step 3a：在檔案**頭部** import block 加新 import
- Step 3b：在檔案**尾部** append handler function

不要在 code block 裡混著 import 和 function——agent 會嘗試在檔案中間插 import。

### 第三方審查審的是 Plan

Codex review 的真正價值是在 code 生出來之前發現問題。這次 M1（`_search_keyword` 簽名寫錯）就是 plan 層的 bug——如果沒有審查，12 個 task 都會基於錯誤的簽名去實作。

## Skill 檔案

### Day 1 就寫

不要等 CLI 做完才寫 skill。開發過程中就該有一份草稿——哪怕只是指令清單 + flag 說明。好處：
- 開發中可以用來驗證「Agent 好不好用」
- Skill 內容跟 CLI 設計同步演進，不會脫節

### Skill 的結構

```markdown
## 指令總覽（速查表）
## 什麼時候用哪個工具（決策表）
## 各指令詳細用法 + 範例
## 常見工作流（多步驟組合）
## 注意事項
```

決策表和工作流比單純列指令更有價值——Agent 不只要知道「怎麼用」，還要知道「什麼時候用哪個」。

### Eval 驗證

用 skill-creator 跑 with-skill vs without-skill 對比。重點不是正確性（baseline 通常也能找到答案），而是效率——工具呼叫次數和時間差距。

## 回顧：如果重來一次

1. **`--json` 從 root callback 透過 Context 傳遞**，不要每個指令重複定義
2. **INVALID_ARGS 用自訂 Click Group subclass 處理**，不要用 `sys.argv` workaround
3. **Skill 和 CLI 同步開發**，不要事後補
4. **Error code 表在 Plan 階段就定義**，不要在開發中逐個發明
