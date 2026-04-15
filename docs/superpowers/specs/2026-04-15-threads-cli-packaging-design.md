# Threads CLI 化（Level 1 + E-輕）— Design Spec

> 建立日期：2026-04-15
> 分支：`feat/cli-packaging`
> 研究依據：`docs/dev/cli-anything-research.md`
> API 實測依據：`docs/dev/api-exploration-results.md`

---

## 目標

把 `threads_pipeline` 的現有功能包裝成可安裝 CLI 工具。

- 使用者打 `threads-advisor plan "題目"` 取代 `python -m threads_pipeline.advisor plan "題目"`
- Agent 可透過 `threads post publish "..." --confirm --yes` 操作 Threads API
- 架構預留未來加入 cli-anything Hub 的相容性

**不做**：新功能、改寫現有邏輯、發佈 PyPI、state 管理、REPL、換 CLI 框架。

---

## 範圍（E-輕）

### 包裝的指令（現有 code 抽出成 CLI 層）

- `threads-advisor plan / review / analyze / list-frameworks` — 現有 advisor
- `threads posts search / list` — 唯讀搜尋
- `threads post insights / replies / publish` — 單篇操作
- `threads post publish-chain` — **串文發文**（重用 publish + reply 組合）
- `threads reply` — 回覆
- `threads account info / insights` — 帳號資訊

### 刻意排除

- 從 advisor plan 結構化資料直接吃（需解析 advisor 輸出格式，屬 E-重）
- 串文自動重試 / 回滾（半途失敗採中斷回報策略，使用者手動處理）
- 發文節流（避免被判 spam，屬 E-重）
- 排程、模板、自動審查、自動紀錄
- 以上屬於 E-重，Level 1 不做。未來可在現有分層架構上擴充。

---

## 架構設計

### 目錄結構

```
threads_pipeline/
├── pyproject.toml                    ← 新增：打包設定
├── threads_pipeline/
│   ├── (現有檔案全不動)
│   └── threads_cli/                  ← 新增
│       ├── __init__.py
│       ├── cli.py                    ← CLI 入口（argparse 子命令）
│       ├── publisher.py              ← 從 demo_publish_reply.py 重構
│       ├── output.py                 ← JSON / 人讀格式化
│       └── SKILL.md                  ← Agent 使用說明（最小可行版）
├── tests/
│   └── test_threads_cli.py           ← 新增
└── CLAUDE.md                         ← 更新 Commands 區塊（雙軌並列）
```

### 分層原則

| 層 | 職責 | 檔案 |
|---|---|---|
| CLI 解析層 | argparse、`--confirm`、`--dry-run`、`--json` | `threads_cli/cli.py` |
| 邏輯層 | 組參數、呼叫 API、處理錯誤 | `threads_cli/publisher.py` |
| API 層 | HTTP 請求、retry、rate limit | 既有 `threads_client.py`（不動） |

**為什麼分層**：為未來 E-重鋪路。E-重的每個新功能都是「在邏輯層加新函式」，不改下層，不改 CLI 層既有指令。

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

[tool.setuptools.packages.find]
include = ["threads_pipeline*"]

[tool.pytest.ini_options]
testpaths = ["threads_pipeline/tests", "tests"]
python_files = ["test_*.py"]

[tool.setuptools.package-data]
"threads_pipeline" = ["templates/*.j2", "references/*.md"]
"threads_pipeline.threads_cli" = ["SKILL.md"]
```

### 三個 entry points 的理由

- `threads-advisor` — 沿用現有 advisor 入口，零破壞
- `threads` — 新 CLI 的主指令
- `cli-anything-threads` — Hub 相容別名（跟 `threads` 同指向），零成本預留未來加入 Hub

### 刻意不加

- `[tool.ruff]` — Level 1 不納入，詳見 research doc 的 roadmap
- `classifiers`、`long_description` — 未發 PyPI 前不必
- `[tool.mypy]` — type hints 尚未完整，加了會全紅

---

## 指令完整表

### `threads-advisor`（現有 advisor，零邏輯改動）

| 指令 | 效果 |
|---|---|
| `threads-advisor plan "題目"` | 產生串文骨架 |
| `threads-advisor review drafts/x.txt` | 審草稿 |
| `threads-advisor review --text "文字"` | inline 審草稿 |
| `threads-advisor analyze` | 數據分析 |
| `threads-advisor list-frameworks` | 列 16+1 框架 |

### `threads`（新）

#### 唯讀（無風險）

| 指令 | Threads API | 實作依據 | 已知限制 |
|---|---|---|---|
| `threads posts search "kw"` | `/me/threads_keyword_search` | `threads_client.fetch_posts` | 中文搜尋回 0、`--author` 無效、`--limit` 上限 50、無 `like_count` |
| `threads posts list --recent N` | `/me/threads` | 待新增 `list_own_posts` | 批次 B 實測 |
| `threads post insights <id>` | `/{post_id}/insights` | `insights_tracker` | 批次 B 實測 |
| `threads post replies <id>` | `/{post_id}/replies` | `demo_publish_reply.py` step 3 | 批次 B 實測 |
| `threads account info` | `/me` | 從 `insights_tracker` 抽出 | 批次 B 實測 |
| `threads account insights` | `/me/threads_insights` | `insights_tracker` | 批次 B 實測 |

全部支援 `--json`，預設是人讀表格。

#### 寫入（強制 dry-run）

| 指令 | Threads API | 實作依據 |
|---|---|---|
| `threads post publish "文字"` | `/me/threads` → `/me/threads_publish` | `demo_publish_reply.py` step 1–2 |
| `threads post publish-chain FILE` | `publish` + `reply`×N 組合 | 重用 publisher 函式 |
| `threads reply <post_id> "內容"` | `/{post_id}/reply` | `demo_publish_reply.py` step 4 |

### `publish-chain` 細節設計

**輸入格式**：每行一則的純文字檔（用 `-` 讀 stdin）

```
# drafts/my-thread.txt
第一則：開頭 hook
第二則：主要內容
第三則：收尾 CTA
```

**執行流程**：
```
第 1 則用 publish → 拿到 first_post_id
第 2 則用 reply 到 first_post_id → 拿到 reply_id_2
第 3 則用 reply 到 reply_id_2 → 拿到 reply_id_3
...（階梯式串）
```

**半途失敗策略**：**中斷並回報**（策略 A）
- 已發的不刪
- 印出「已發 post_id 清單」+「失敗那則的錯誤訊息」
- exit 1
- 使用者自行決定：(a) 手動刪除已發、(b) 手動補發剩餘、(c) 忽略

**為什麼不自動重試 / 回滾**：需要狀態管理 + 錯誤恢復邏輯，屬 E-重範圍。

**dry-run 輸出範例**：
```
[DRY RUN] Would publish chain of 3 posts to @azuma520:
─────────────────────────────────
1/3 (opener):   第一則：開頭 hook（14 chars）
2/3 (reply):    第二則：主要內容（16 chars）
3/3 (reply):    第三則：收尾 CTA（13 chars）
─────────────────────────────────
Total: 3 posts, 43 chars
Account: azuma520 (ID: ...)

Add --confirm to actually publish.
```

**字數限制檢查**：發送前每則都檢查是否超過 500 字元，任一則超過就**拒絕整串**（全有或全無，比半途失敗乾淨）。

#### 系統輔助

`threads --version` / `threads --help` / `threads <sub> --help`

### 命名慣例

- 動詞放最後（`posts search`、`post publish`、`account info`）
- 單數操作單項（`post publish`）、複數操作列表（`posts search`）

---

## 安全機制（寫入指令專屬）

### 四層防護

| 層 | 觸發 | 行為 |
|---|---|---|
| 1. Token 檢查 | 每次 API 呼叫前 | Token 不存在或無效 → exit 1 |
| 2. 預設 dry-run | 沒加 `--confirm` | 只印「會發什麼」、不呼叫 API |
| 3. 互動確認 | 加了 `--confirm` 沒加 `--yes` | 互動式二次確認（預設 N） |
| 4. Agent 模式 | `--confirm --yes` | 跳過互動、直接呼叫 API |

### 安全層級總表

| 指令參數 | 行為 |
|---|---|
| `publish "x"` | dry-run（只印） |
| `publish "x" --confirm` | 印 + 互動確認（按 y 才發） |
| `publish "x" --confirm --yes` | 直接發（Agent） |
| `publish "x" --yes`（單用） | 仍 dry-run（`--yes` 無 `--confirm` 無效） |

### dry-run 輸出必含

- 發文目標帳號（防發錯 token）
- 字數（防超過 500 上限）
- Token 剩餘天數（防 confirm 後才發現過期）

### 主動警告（UX）

| 情境 | 行為 |
|---|---|
| 中文關鍵字搜尋回 0 | 印警告 + 建議用英文 + 引 `api-exploration-results.md §9` |
| 使用者試圖用 `--author` | **不提供此 flag**（最好的 UX 就是不讓使用者打錯） |
| `--limit > 50` | clamp 到 50 + 印提示 |

### 沿用既有基礎

- `threads_client._request_with_retry` — 處理 429、5xx、timeout
- `threads_client` 的 Token 驗證 / 續期邏輯

---

## 遷移路徑

### 雙軌並行

| 做法 | 舊（繼續可用） | 新（推薦） |
|---|---|---|
| 產串文 | `python -m threads_pipeline.advisor plan "題目"` | `threads-advisor plan "題目"` |
| 審草稿 | `python -m threads_pipeline.advisor review drafts/x.txt` | `threads-advisor review drafts/x.txt` |
| 分析 | `python -m threads_pipeline.advisor analyze` | `threads-advisor analyze` |
| 每日 pipeline | `python -m threads_pipeline.main` | 維持舊法，不 CLI 化 |

**舊用法 Level 1 期間永不廢除**。

### CLAUDE.md 更新

在 Commands 區塊列新版（推薦）+ 舊版（相容保留）。

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
pytest threads_pipeline/tests/
pytest threads_pipeline/tests/evals/ --run-llm-evals  # 可選
```

既有測試變紅就 revert。

### Layer 2：新 CLI 層單元測試（`tests/test_threads_cli.py`）

覆蓋範圍：

- argparse 解析（正常輸入、錯誤輸入）
- dry-run 不呼叫 API（mock）
- `--confirm` 互動確認（mock `input()`）
- `--yes` 跳過互動
- Token 缺失 → exit 1
- API 錯誤 → 分層錯誤訊息
- `--json` 輸出合法

全部 mock，不打真 API。

### Layer 3：手動 smoke test

Level 1 完成後執行一次：

1. `pip install -e .` → `where threads-advisor` 驗證
2. 雙軌對照（新舊指令產出應一致）
3. `threads post publish "測試"` 確認 dry-run（不發）
4. `threads post publish "[CLI test]" --confirm --yes` 實發一則 → Threads 網站驗證 → 手動刪除
5. `THREADS_ACCESS_TOKEN=` 驗證 exit 1

### 測試不做

- 自動 E2E 打真 API（會產生垃圾發文）
- mutation testing / fuzzing
- 效能測試
- 跨平台測試

---

## 實作執行順序（批次 A）

```
① 寫 pyproject.toml
② pip install -e ".[dev]"、驗證 threads-advisor 存在
③ 驗證既有 pytest 通過
④ 建立 threads_cli/ 骨架（空實作）
⑤ 寫 argparse 解析測試（TDD）
⑥ 實作 cli.py 子命令註冊（含 publish-chain）
⑦ 從 demo_publish_reply.py 抽出 publisher.publish_text / reply_to
⑧ 實作 publisher.publish_chain（組合 publish_text + reply_to）
⑨ 寫 dry-run / confirm / --yes 測試（單則 + 串文）
⑩ 實作安全層，讓測試通過
⑪ 手動 smoke test（實發一則 + 3 則串文、刪除）
⑫ 更新 CLAUDE.md
⑬ commit + 準備 merge
```

批次 B（list / insights / replies / account）Level 1 批次 A merge 後再開新 session 做。

---

## 失敗回退

因為 Level 1 **純粹新增**（新檔 + 新指令），既有 code 一行沒改，revert 極簡單：

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
| Meta Threads API 官方文檔 https://developers.facebook.com/docs/threads | API endpoint、參數、權限、限速。每個新指令實作前先查 |
| `docs/dev/cli-anything-research.md` | 架構決策的研究依據 |
| `docs/dev/api-exploration-results.md` | 本專案既有 API 實測結果 |
| `scripts/demo_publish_reply.py` | 發文 / 回覆邏輯的參考 |
| `threads_pipeline/threads_client.py` | 既有 API client，`_request_with_retry` 模式 |
| `threads_pipeline/insights_tracker.py` | insights 相關邏輯 |
| `../cli-anything-ref/` | cli-anything 本地 sparse clone |

---

## 驗收條件（Level 1 批次 A 完成的標準）

全部達成才算 done：

- [ ] `pyproject.toml` 已建立且 `pip install -e ".[dev]"` 成功
- [ ] `threads-advisor`、`threads`、`cli-anything-threads` 三個指令都能執行
- [ ] 既有 pytest 全部通過（零 regression）
- [ ] `tests/test_threads_cli.py` 新測試全部通過
- [ ] `threads-advisor list-frameworks` 輸出與 `python -m threads_pipeline.advisor list-frameworks` 相同
- [ ] `threads post publish "x"`（無 `--confirm`）絕對不發文
- [ ] `threads post publish "..." --confirm --yes` 實發一則測試文並成功（手動驗證）
- [ ] `threads post publish-chain FILE --confirm --yes` 實發 3 則串文並手動刪除（手動驗證）
- [ ] publish-chain 半途失敗時會「中斷並回報已發 ID」（可 mock 測試）
- [ ] Token 缺失時 exit 1 且有清楚錯誤訊息
- [ ] CLAUDE.md Commands 區塊已更新為雙軌並列
- [ ] `threads_cli/SKILL.md` 最小版已寫（Agent 可讀）

批次 B 另計驗收條件（後續 session 定）。

---

## 未來 roadmap（超出 Level 1 範圍）

### 短期
- Ruff 納入 pyproject.toml（詳見 research doc 的 roadmap 章節）
- 實作批次 B 指令（list / insights / replies / account）

### 中期（E-重）
- 從 advisor plan 結構化資料直接發串文（接管 plan 輸出）
- 串文自動重試 / 回滾
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
- ❌ 跨平台測試
- ❌ 自動化 E2E（避免垃圾發文）
