# Threads CLI 化（Level 1 + E-輕）— Design Spec

> 建立日期：2026-04-15
> 修訂日期：2026-04-15（實測 + 雙審查後）
> 分支：`feat/cli-packaging`
> 研究依據：`docs/dev/cli-anything-research.md`
> API 實測依據：`docs/dev/api-exploration-results.md`

---

## 修訂紀錄

**v1.0 → v1.1（審查後修訂）**：

- 修正 repo 為扁平 layout（非巢狀），`pyproject.toml` 改用 `package-dir` mapping
- 修正 search endpoint 為 `/keyword_search`（非 `/me/threads_keyword_search`）
- 修正 reply 為兩階段流程 + `reply_to_id`（非虛構的 `/{post_id}/reply`）
- 確認 reply 需從零寫（`demo_publish_reply.py` 沒有 reply 實作）
- 新增 DELETE endpoint 實測確認，rollback 技術可行（Level 1 仍只 stub）
- limit 統一用 25 上限（遵照既有 `threads_client.py:75`）
- 架構：`publisher.py` 提到 package root（跟 `threads_client.py` 同層）
- 安全：非 TTY 環境下 `--confirm` 拒絕執行；`--yes` 沒 `--confirm` hard-error
- 新增 `--on-failure=stop|retry|rollback` 預留介面（只實作 stop）
- 新增 cli.py dispatch table 寫法要求
- 新增 SKILL.md 最小內容定義
- 新增 Windows UTF-8 setdefault 要求

---

## 目標

把 `threads_pipeline` 的現有功能包裝成可安裝 CLI 工具。

- 使用者打 `threads-advisor plan "題目"` 取代 `python -m threads_pipeline.advisor plan "題目"`
- Agent 可透過 `threads post publish "..." --confirm --yes` 操作 Threads API
- 架構預留未來加入 cli-anything Hub 的相容性

**不做**：新功能、改寫現有邏輯、發佈 PyPI、state 管理、REPL、換 CLI 框架。

---

## 範圍（E-輕）

### 包裝的指令

- `threads-advisor plan / review / analyze / list-frameworks` — 現有 advisor
- `threads posts search / list` — 唯讀搜尋
- `threads post insights / replies / publish / publish-chain` — 單篇操作
- `threads reply` — 回覆
- `threads account info / insights` — 帳號資訊

### 刻意排除

- 從 advisor plan 結構化資料直接發串文（需解析 advisor 輸出格式，屬 E-重）
- 串文自動重試 / 自動 rollback（Level 1 只實作 stop 策略；flag 預留）
- 發文節流（避免被判 spam，屬 E-重）
- 排程、模板、自動審查、自動紀錄

以上屬於 E-重，Level 1 不做。未來可在現有分層架構上擴充。

---

## 架構設計

### 目前 repo 實況（扁平 layout）

```
桌面/
└── threads_pipeline/                 ← 既是 repo root，也是 Python package
    ├── __init__.py                   ← 1 行，使 threads_pipeline 成為 package
    ├── advisor.py
    ├── analyzer.py
    ├── db_helpers.py
    ├── insights_tracker.py
    ├── main.py
    ├── report.py
    ├── threads_client.py
    ├── templates/
    ├── references/
    ├── tests/                        ← 既有測試在 repo root 的 tests/
    └── scripts/
```

**關鍵事實**：
- `threads_pipeline` 作為 Python package 的名稱，來自「parent 目錄 `桌面/`」提供的 namespace
- 現在可以 `from threads_pipeline.advisor import ...`，是因為 `桌面/` 在 Python path 上
- `pip install -e .` 要 work，需要明確告訴 setuptools「當前目錄就是 `threads_pipeline` package」

### CLI 化後的目錄結構

```
threads_pipeline/                     ← repo + package root
├── pyproject.toml                    ← 新增
├── __init__.py                       ← 現有，保留
├── advisor.py                        ← 不動
├── analyzer.py                       ← 不動
├── threads_client.py                 ← 不動（API client）
├── insights_tracker.py               ← 不動
├── main.py                           ← 不動
├── report.py                         ← 不動
├── db_helpers.py                     ← 不動
│
├── publisher.py                      ← 新增：發文邏輯（從 demo 抽出）
│
├── threads_cli/                      ← 新增：CLI 層
│   ├── __init__.py
│   ├── cli.py                        ← argparse dispatch table
│   ├── output.py                     ← JSON / 人讀格式化
│   └── SKILL.md                      ← Agent 使用說明
│
├── tests/                            ← 既有
│   └── test_threads_cli.py           ← 新增
│
├── scripts/
│   └── demo_publish_reply.py         ← 暫留作 reference，未來可 deprecate
│
└── CLAUDE.md                         ← 更新 Commands 區塊
```

### 為什麼 `publisher.py` 在 package root 而非 `threads_cli/` 底下

**理由**：`publisher.py` 是**純 API 邏輯**（呼叫 Threads API、處理 retry、處理 container 流程），跟 argparse 無關。

把它放 root 跟 `threads_client.py` 同層：
1. 任何人想用 publish 功能，`from threads_pipeline.publisher import publish_text` 直接可用
2. 未來 `advisor.py` 想加「產完 plan 直接發文」，不需要跨進 CLI 層 import
3. 單元測試可以獨立測 publisher，不用 mock CLI

`threads_cli/` 只放**真正屬於 CLI 的東西**（argparse 解析、輸出格式化、SKILL.md）。

### 三層分工

| 層 | 職責 | 檔案 |
|---|---|---|
| CLI 解析層 | argparse、`--confirm`、`--dry-run`、`--json` | `threads_cli/cli.py` |
| 邏輯層 | 組參數、呼叫 API、處理 container 流程、錯誤處理 | `publisher.py`（新）、`threads_client.py`（既有） |
| API 層 | HTTP 請求、retry、rate limit | `threads_client.py` 的 `_request_with_retry` |

---

## `pyproject.toml` 完整內容

```toml
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "threads-pipeline"
version = "0.1.0"
description = "Threads API operations & post advisor (CLI-Anything compatible)"
requires-python = ">=3.13"
readme = "README.md"
license = {text = "MIT"}
authors = [{name = "azuma520"}]
keywords = ["threads", "meta", "cli", "agent", "social-media"]

dependencies = [
    "requests>=2.31",
    "pyyaml>=6.0",
    "jinja2>=3.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
]

[project.scripts]
threads-advisor      = "threads_pipeline.advisor:main"
threads              = "threads_pipeline.threads_cli.cli:main"
cli-anything-threads = "threads_pipeline.threads_cli.cli:main"

[project.urls]
Homepage   = "https://github.com/azuma520/threads_pipeline"
Repository = "https://github.com/azuma520/threads_pipeline"
Issues     = "https://github.com/azuma520/threads_pipeline/issues"

# ─────────────────────────────────────────────────
# 扁平 layout 的套件設定
# 告訴 setuptools：當前目錄 (.) 就是 threads_pipeline package 的內容
# ─────────────────────────────────────────────────
[tool.setuptools]
package-dir = {"threads_pipeline" = "."}

[tool.setuptools.packages.find]
where = ["."]
include = ["threads_cli*"]
# 只 find threads_cli 子模組；root 層檔案由 package-dir 涵蓋

[tool.setuptools.package-data]
"threads_pipeline" = ["templates/*.j2", "references/*.md"]
"threads_pipeline.threads_cli" = ["SKILL.md"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

### 關鍵設定說明

**`package-dir = {"threads_pipeline" = "."}`**
這一行是扁平 layout 的關鍵。翻譯：「告訴 setuptools，`threads_pipeline` 這個 package 的 code 就在當前目錄 `.`。」

**`packages.find` + `include = ["threads_cli*"]`**
讓 setuptools 找到 `threads_cli/` 子模組，識別為 `threads_pipeline.threads_cli`。

**`testpaths = ["tests"]`**（單一路徑）
既有 tests 在 repo root 的 `tests/`，不在 `threads_pipeline/tests/`（此為 CLAUDE.md 舊誤植）。

**三個 entry points 的理由**

- `threads-advisor` — 沿用現有 advisor 入口
- `threads` — 新 CLI 的主指令
- `cli-anything-threads` — Hub 相容別名（用戶保留此選項）

---

## 指令完整表

### `threads-advisor`（現有，零改動）

| 指令 | 效果 |
|---|---|
| `threads-advisor plan "題目"` | 產生串文骨架 |
| `threads-advisor review drafts/x.txt` | 審草稿 |
| `threads-advisor review --text "文字"` | inline 審草稿 |
| `threads-advisor analyze` | 數據分析 |
| `threads-advisor list-frameworks` | 列 16+1 框架 |

### `threads`（新增）

#### 唯讀（無風險）

| 指令 | HTTP | Threads API | 實作依據 | 備註 |
|---|---|---|---|---|
| `threads posts search "kw"` | GET | `/keyword_search` | `threads_client.fetch_posts` | 中文搜尋回 0；無 `like_count`；limit cap 25 |
| `threads posts list --recent N` | GET | `/me/threads` | `demo_publish_reply.py` step 4 | 列自己貼文 |
| `threads post insights <id>` | GET | `/{post_id}/insights` | `insights_tracker` | 批次 B 實測 |
| `threads post replies <id>` | GET | `/{post_id}/replies` | `demo_publish_reply.py` step 3 | 列出該貼文的回覆 |
| `threads account info` | GET | `/me` | 從 `insights_tracker` 抽 | 基本帳號資訊 |
| `threads account insights` | GET | `/me/threads_insights` | `insights_tracker` | 批次 B 實測 |

全部支援 `--json`。`--limit` 超過 25 時 clamp + 印警告（stderr / JSON envelope）。

#### 寫入（強制 dry-run）

| 指令 | API 流程 | 實作依據 |
|---|---|---|
| `threads post publish "文字"` | 兩階段：POST `/me/threads` → POST `/me/threads_publish` | `demo_publish_reply.py` step 1-2 |
| `threads post publish-chain FILE` | `publish` + `reply`×N 組合 | 重用 publisher 函式 |
| `threads reply <post_id> "內容"` | 兩階段：POST `/me/threads` (with `reply_to_id`) → POST `/me/threads_publish` | **從零寫**（demo 沒 reply 實作） |

#### 危險操作 Stub（Level 1 不實作，但保留介面）

| 指令 | 預期 API | 狀態 |
|---|---|---|
| `threads post delete <id>` | `DELETE /{post_id}`（demo step 5 已驗證存在） | **Level 1 不實作**；但 `publish-chain` 的 rollback 依賴它，批次 B 評估 |

#### 系統輔助

`threads --version` / `threads --help` / `threads <sub> --help`

### 命名慣例

- 動詞放最後（`posts search`、`post publish`、`account info`）
- 單數操作單項、複數操作列表

---

## Publish / Reply 兩階段 API 流程

### `publish_text(text)` — 單則發文

```
Step 1  POST https://graph.threads.net/v1.0/me/threads
        params: access_token, media_type=TEXT, text=<text>
        → 回傳 container_id

Step 2  POST https://graph.threads.net/v1.0/me/threads_publish
        params: access_token, creation_id=<container_id>
        → 回傳 post_id
```

### `reply_to(post_id, text)` — 回覆既有貼文

```
Step 1  POST https://graph.threads.net/v1.0/me/threads
        params: access_token, media_type=TEXT, text=<text>,
                reply_to_id=<post_id>      ← 關鍵差異
        → 回傳 container_id

Step 2  POST https://graph.threads.net/v1.0/me/threads_publish
        params: access_token, creation_id=<container_id>
        → 回傳 reply_post_id
```

**publish 和 reply 共用 90% 邏輯**，step 1 多一個 `reply_to_id` 即可。

### 兩階段之間的錯誤處理

| 失敗點 | 行為 |
|---|---|
| Step 1 失敗 | 印錯誤、exit 1、**不呼叫 step 2** |
| Step 1 成功、Step 2 失敗 | 印錯誤 + `container_id`（孤兒）、exit 1、**不自動清理**（container 會在 Meta 側自然過期） |

**不做 status polling**：Level 1 採 best-effort 模式 — step 1 成功後立刻 step 2。Meta 文檔建議的 30 秒等待是 media 用（你都是純文字），文字通常不用等。若未來出現 race condition 錯誤，再加 polling。

---

## `publish-chain` 細節設計

### 輸入格式

每行一則的純文字檔（用 `-` 讀 stdin）：

```
# drafts/my-thread.txt
第一則：開頭 hook
第二則：主要內容
第三則：收尾 CTA
```

### 階梯式串連流程（web 搜尋已確認）

```
第 1 則：publish_text(text_1)          → first_post_id
第 2 則：reply_to(first_post_id, text_2)   → reply_id_2
第 3 則：reply_to(reply_id_2, text_3)      → reply_id_3
...（每則 reply 到前一則，形成階梯）
```

### 字數 pre-flight 檢查

送出前先檢查每則是否超過 500 字元，**任一則超過就拒絕整串**（全有或全無 — 此為 pre-flight，成本為零）。

### 半途失敗策略：`--on-failure`

```
--on-failure=stop        ← Level 1 預設且唯一實作
--on-failure=retry       ← Level 1 保留介面，呼叫時拋 NotImplementedError
--on-failure=rollback    ← Level 1 保留介面，呼叫時拋 NotImplementedError
```

**為何預留其他選項**：避免未來加功能時破壞既有 agent script 的 CLI 呼叫契約。

**stop 語義**：
- 已發的不刪（DELETE endpoint 技術上可行但 Level 1 不自動做）
- 印出「已發 post_id 清單 + 失敗那則的錯誤」
- exit 1
- 使用者自行決定：(a) 手動刪除已發、(b) 手動補發剩餘、(c) 忽略

**和 pre-flight 的不對稱**：pre-flight「全有或全無」（字數檢查，零成本），但 mid-flight「中斷回報」（API 呼叫已發生，回滾有成本）。**這是刻意的不對稱，不是遺漏**。

### dry-run 輸出範例

```
[DRY RUN] Would publish chain of 3 posts to @azuma520:
─────────────────────────────────
1/3 (opener):   第一則：開頭 hook（14 chars）
2/3 (reply):    第二則：主要內容（16 chars）
3/3 (reply):    第三則：收尾 CTA（13 chars）
─────────────────────────────────
Total: 3 posts, 43 chars
Account: azuma520 (ID: ...)
On-failure policy: stop

Add --confirm to actually publish.
```

---

## 安全機制（寫入指令專屬）

### 四層防護

| 層 | 觸發 | 行為 |
|---|---|---|
| 1. Token 檢查 | CLI 啟動時 once | Token 不存在 → exit 1；中途 401/403 由 `_request_with_retry` surface |
| 2. 預設 dry-run | 沒加 `--confirm` | 只印「會發什麼」、不呼叫 API |
| 3. 互動確認 | 加了 `--confirm` 沒加 `--yes`（TTY） | 互動式二次確認（預設 N） |
| 4. Agent 模式 | `--confirm --yes` | 跳過互動、直接呼叫 API |

### Flag 組合語義表（v1.1 修訂）

| 參數 | TTY 環境 | 非 TTY 環境（CI / pipe / agent） |
|---|---|---|
| `publish "x"` | dry-run | dry-run |
| `publish "x" --confirm` | 印 + 互動確認（按 y 才發） | **hard-error exit 2**（`--confirm without --yes in non-TTY`）|
| `publish "x" --confirm --yes` | 直接發 | 直接發 |
| `publish "x" --yes`（單用） | **hard-error exit 2**（`--yes requires --confirm`） | **hard-error exit 2** |

**v1.1 變更**：`--yes` 無 `--confirm` 不再是靜默 dry-run，而是 hard-error。理由：agent 工作流中有 `--yes` 從別處來（config / 環境變數）、`--confirm` 從別處來的情況，若 `--confirm` 缺失應讓使用者立刻知道，不是靜默吞下去。

### 非 TTY 檢測

```python
import sys
if not sys.stdin.isatty() and args.confirm and not args.yes:
    print("Error: --confirm requires --yes in non-interactive environments", file=sys.stderr)
    sys.exit(2)
```

### dry-run 輸出必含

- 發文目標帳號（防發錯 token）
- 字數（防超過 500 上限）
- Token 剩餘天數（若 `threads_client` 可取得；取不到則印 `unknown`）
- On-failure policy（for chain）

### Token 過期提前警告

任何指令（不只寫入）若偵測到 Token 剩餘 < 7 天，都在 stderr 印警告：

```
⚠ Your Threads access token expires in 5 days. Renew at:
  https://developers.facebook.com/tools/access-token-tool/
```

### 主動警告（UX）

| 情境 | 行為 |
|---|---|
| 中文關鍵字搜尋回 0 | 警告 + 建議英文 + 引 `api-exploration-results.md §9` |
| `--author` flag | **不提供此 flag**；未來 Advanced Access 核准後 re-evaluate |
| `--limit > 25` | Clamp 到 25 + 提示「API allows up to 50 but project caps at 25; see `threads_client.py:75`」 |

### 沿用既有基礎

- `threads_client._request_with_retry` — 處理 429、5xx、timeout
- `threads_client` 的 Token 驗證 / 續期邏輯

---

## CLI 實作要求（cli.py 結構）

### Dispatch table 寫法

`cli.py` 必須用 dispatch table 註冊子命令，**不要寫 god-function 的 if/elif 串**：

```python
# threads_cli/cli.py 結構示意
COMMANDS = {
    "posts.search":      cmd_posts_search,
    "posts.list":        cmd_posts_list,
    "post.insights":     cmd_post_insights,
    "post.replies":      cmd_post_replies,
    "post.publish":      cmd_post_publish,
    "post.publish-chain":cmd_post_publish_chain,
    "reply":             cmd_reply,
    "account.info":      cmd_account_info,
    "account.insights":  cmd_account_insights,
}

def main() -> int:
    args = _parse_args()
    cmd_fn = COMMANDS.get(args._cmd_key)
    if cmd_fn is None:
        ...
    return cmd_fn(args)

def cmd_posts_search(args) -> int:
    # 每個子命令各自的實作
    ...
```

**好處**：
- 測試可以直接呼叫 `cmd_posts_search(args)`，不用跑整個 argparse
- 未來若要換 click / Typer，dispatch table 改裝飾器掛在同樣的 cmd_* 函式，機械化遷移
- 新增子命令只要加一筆 dict entry + 一個 cmd_ 函式

### Windows UTF-8 setdefault

所有新 CLI 入口（`threads_cli/cli.py`、`publisher.py` 若獨立執行）都要在模組頂部：

```python
import os
os.environ.setdefault("PYTHONUTF8", "1")
```

理由：避免 Windows cp950 在印中文/box-drawing 字元時 mojibake（`main.py:14` 已有此 pattern，沿用）。

### Exit codes

| Exit code | 情境 |
|---|---|
| 0 | 成功 / dry-run 完成 / 使用者在互動確認時拒絕 |
| 1 | API 失敗 / 網路錯誤 / 執行階段錯誤 |
| 2 | 使用者用法錯誤（argparse 預設 / `--confirm --yes` 組合錯誤） |

---

## `SKILL.md` 最小內容定義

`threads_pipeline/threads_cli/SKILL.md` 必含：

```markdown
---
name: threads-cli
description: 一句話說明
---

## 指令索引

- `threads posts search <kw>` — ...
- `threads post publish <text>` — ...
（完整列表）

## 安全契約（Agent 模式）

寫入指令必須用 `--confirm --yes` 才會真的執行：
- `threads post publish "..." --confirm --yes`
- `threads reply <id> "..." --confirm --yes`
- `threads post publish-chain file.txt --confirm --yes`

沒加 `--yes` 在非 TTY 環境會 hard-error（不是靜默 dry-run）。

## 輸出格式

所有查詢指令支援 `--json` 切換。

## 已知限制

- 中文關鍵字搜尋會回 0 筆（用英文）
- `--limit` 上限 25（專案設定）
- 詳見 `docs/dev/api-exploration-results.md`

## 詳細文檔

- 完整 API 對照：`docs/superpowers/specs/2026-04-15-threads-cli-packaging-design.md`
- API 實測結果：`docs/dev/api-exploration-results.md`
```

Level 1 只要填到這個骨架就算完成；豐富化留給未來加入 Hub 時做。

---

## 遷移路徑

### 雙軌並行

| 做法 | 舊（繼續可用） | 新（推薦） |
|---|---|---|
| 產串文 | `python -m threads_pipeline.advisor plan "題目"` | `threads-advisor plan "題目"` |
| 審草稿 | `python -m threads_pipeline.advisor review drafts/x.txt` | `threads-advisor review drafts/x.txt` |
| 分析 | `python -m threads_pipeline.advisor analyze` | `threads-advisor analyze` |
| 每日 pipeline | `python -m threads_pipeline.main` | 維持舊法 |

舊用法 Level 1 期間永不廢除。

### CLAUDE.md 更新

Commands 區塊列新版（推薦）+ 舊版（相容保留）。

### 安裝流程

```bash
cd 桌面/threads_pipeline
pip install -e ".[dev]"
threads-advisor --help
threads --help
```

---

## 測試策略（三層）

### Layer 1：既有測試不能爛

```bash
pytest
```

既有測試變紅就 revert。

### Layer 2：新 CLI 層單元測試（`tests/test_threads_cli.py`）

覆蓋：

- argparse 解析（正常 / 錯誤輸入）
- dry-run 不呼叫 API（mock）
- `--confirm` 互動確認（mock `input()`）
- `--yes` 跳過互動
- **`--yes` 單用 hard-error exit 2**
- **非 TTY 環境 `--confirm` 無 `--yes` hard-error exit 2**
- Token 缺失 → exit 1
- API 錯誤 → 分層錯誤訊息
- `--json` 輸出合法
- `publish-chain` 字數 pre-flight 拒絕整串
- `publish-chain` mid-flight 失敗「已發 IDs」印出 + exit 1
- `--on-failure=retry|rollback` 目前回 NotImplementedError

全部 mock，不打真 API。

### Layer 3：手動 smoke test

Level 1 完成後執行一次：

1. `pip install -e .` → `where threads-advisor` / `where threads` / `where cli-anything-threads`
2. 雙軌對照（新舊指令產出應一致）：
   ```bash
   threads-advisor list-frameworks > new.txt
   python -m threads_pipeline.advisor list-frameworks > old.txt
   diff new.txt old.txt
   ```
3. `threads post publish "測試"` 確認 dry-run（不發）
4. `threads post publish "[CLI test]" --confirm --yes` 實發 → Threads 網站驗證 → 手動刪除
5. `threads post publish-chain drafts/smoke-test.txt --confirm --yes` 實發 3 則串文 → 驗證階梯式 reply → 手動刪除
6. `THREADS_ACCESS_TOKEN=` 驗證 exit 1
7. `echo "a" | threads post publish a --confirm` 驗證非 TTY + `--confirm` 無 `--yes` → exit 2

### 測試不做

- 自動 E2E 打真 API（會產生垃圾發文）
- mutation testing / fuzzing
- 效能測試
- 跨平台測試（只驗 Windows）

---

## 實作執行順序（批次 A）

```
① 寫 pyproject.toml + 驗證 pip install -e ".[dev]" 成功
② 驗證既有 pytest 通過
③ 建立 threads_cli/ 骨架（空實作 + dispatch table）
④ 抽出 publisher.py（publish_text 從 demo step 1-2）
⑤ 從零寫 publisher.reply_to（demo 無此 code）
⑥ 寫 publisher.publish_chain（組合 publish_text + reply_to）
⑦ 寫 argparse 解析測試（TDD）
⑧ 實作 cli.py 子命令註冊（含 publish-chain、--on-failure stub）
⑨ 寫 dry-run / confirm / --yes / 非 TTY 測試
⑩ 實作安全層
⑪ 寫 SKILL.md 最小版
⑫ 手動 smoke test（實發一則 + 3 則串文、刪除）
⑬ 更新 CLAUDE.md
⑭ commit + 準備 merge
```

批次 B（list / insights / replies / account / delete）Level 1 批次 A merge 後再開新 session 做。

---

## 失敗回退

Level 1 純粹新增（新檔 + 新指令），既有 code 一行沒改，revert 簡單：

```bash
# 選項 1：revert 特定 commits
# 選項 2：放棄整個分支
git checkout main && git branch -D feat/cli-packaging
# 選項 3：暫停
git commit -am "WIP" && # 未來接續
```

---

## 外部參考資源

| 資源 | 用途 |
|---|---|
| Meta Threads API 官方文檔 https://developers.facebook.com/docs/threads | API endpoint、參數、權限。每個新指令實作前先查 |
| `docs/dev/cli-anything-research.md` | 架構決策的研究依據 |
| `docs/dev/api-exploration-results.md` | 本專案既有 API 實測結果 |
| `scripts/demo_publish_reply.py` | publish / replies list / delete 的參考（reply 需從零寫） |
| `threads_pipeline/threads_client.py` | 既有 API client、`_request_with_retry` |
| `threads_pipeline/insights_tracker.py` | insights 相關邏輯 |
| `../cli-anything-ref/` | cli-anything 本地 sparse clone |

---

## 驗收條件（Level 1 批次 A 完成的標準）

全部達成才算 done：

- [ ] `pyproject.toml` 已建立且 `pip install -e ".[dev]"` 成功（驗證扁平 layout 設定正確）
- [ ] `threads-advisor`、`threads`、`cli-anything-threads` 三個指令都能執行
- [ ] 既有 pytest 全部通過（零 regression）
- [ ] `tests/test_threads_cli.py` 新測試全部通過
- [ ] `threads-advisor list-frameworks` 輸出與 `python -m threads_pipeline.advisor list-frameworks` 相同
- [ ] `threads post publish "x"`（無 `--confirm`）絕對不發文
- [ ] `threads post publish "..." --confirm --yes` 實發一則測試文並成功（手動驗證 + 刪除）
- [ ] `threads reply <post_id> "..." --confirm --yes` 實發一則回覆並成功（手動驗證 + 刪除）
- [ ] `threads post publish-chain FILE --confirm --yes` 實發 3 則串文並驗證階梯式 reply 結構（手動驗證 + 刪除）
- [ ] `publish-chain` 半途失敗時會「中斷並回報已發 IDs」（mock 測試）
- [ ] `--on-failure=retry` 和 `--on-failure=rollback` 呼叫時回 NotImplementedError（保留介面）
- [ ] `--yes` 無 `--confirm` hard-error exit 2
- [ ] 非 TTY 環境 `--confirm` 無 `--yes` hard-error exit 2
- [ ] Token 缺失時 exit 1 且有清楚錯誤訊息
- [ ] CLAUDE.md Commands 區塊已更新為雙軌並列
- [ ] `threads_cli/SKILL.md` 最小版已寫（含指令索引 / 安全契約 / 輸出格式 / 已知限制）

批次 B 另計驗收條件（後續 session 定）。

---

## 未來 roadmap（超出 Level 1 範圍）

### 短期
- Ruff 納入 pyproject.toml（詳見 research doc）
- 實作批次 B 指令（list / insights / replies / account / **delete**）
- 評估是否把 `threads_client.py:75` 的 25 上限提高到 50

### 中期（E-重）
- 從 advisor plan 結構化資料直接發串文（接管 plan 輸出）
- `--on-failure=retry`（指數退避重試 429/5xx）
- `--on-failure=rollback`（呼叫 DELETE 清理已發）
- 發文節流（每則間隔 N 秒，避免被判 spam）
- 排程、模板、發前自動 review、發後自動紀錄

### 遠期（加入 Hub）
- 撰寫完整 `SKILL.md`
- 對 HKUDS/CLI-Anything 發 registry-only PR
- 考慮發佈 PyPI

---

## 本 spec 刻意排除的項目（明示 YAGNI）

- ❌ 改 argparse → click / Typer
- ❌ 改 pip → uv
- ❌ 加 Pydantic / FastAPI / Docker
- ❌ 發佈到 PyPI
- ❌ Session / undo / REPL
- ❌ AI 內容審查、重複發文偵測、自動排程
- ❌ 跨平台測試（只驗 Windows）
- ❌ 自動化 E2E（避免垃圾發文）
- ❌ publish 兩階段之間 container status polling（Level 1 best-effort）
- ❌ `threads post delete` 的 CLI 實作（Level 1 僅記錄 API 存在；批次 B 評估）
