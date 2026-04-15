# CLI-Anything 研究筆記

> 目的：評估 `HKUDS/CLI-Anything` 的設計模式，作為 `threads_pipeline` CLI 化的參考。
> 參考原始碼位置：`../cli-anything-ref/`（shallow + sparse clone，884K）
> 建立日期：2026-04-15

## TL;DR（給未來的自己）

CLI-Anything 的核心理念：**讓所有軟體變成 Agent-Native**。
把原本只有 GUI 的軟體（GIMP、Blender、Obsidian…）或只有 REST API 的服務，
統一包裝成「stateful + undoable + JSON 友善」的 CLI，讓 AI Agent 能直接操作。

它不是重寫這些軟體，而是在上面加一層**薄薄的 CLI harness**。

---

## 研究範圍

本研究 sparse-clone 了以下子目錄作為樣本：

- `cli-hub/` — Hub 本體（套件管理器）
- `cli-hub-meta-skill/` — 教 Agent 使用 Hub 的 meta skill
- `skill_generation/` — 自動生成新 CLI harness 的工具
- `mermaid/agent-harness/` — 最簡單的 harness 範例
- `obsidian/agent-harness/` — 跟本專案筆記流程相近的 harness
- `registry.json` — 所有 CLI 的 metadata 清單

---

## 外部參考資源（實作時必看）

| 資源 | 用途 | 連結 / 路徑 |
|---|---|---|
| **Meta Threads API 官方文檔** | API endpoint、參數、權限、限速規則 | https://developers.facebook.com/docs/threads |
| cli-anything monorepo | harness 參考實作 | https://github.com/HKUDS/CLI-Anything |
| 本地 sparse clone | mermaid / obsidian / cli-hub 樣本 | `../cli-anything-ref/` |
| 本專案 API 探索結果 | 已知限制與實測發現 | `docs/dev/api-exploration-results.md` |

**開發新指令的標準流程**：
1. 先讀 Meta 官方文檔確認該 endpoint 的最新參數 / 權限需求
2. 對照 `docs/dev/api-exploration-results.md` 看本專案過往實測發現什麼限制
3. 實作時參考 `threads_client.py` 現有 `_request_with_retry` 模式

---

## Step 1：`registry.json` — CLI entry 的 Schema

### 名詞快速理解

- **`registry.json`** = CLI 工具的「商品目錄」，整個 Hub 的 50+ CLI 都記錄在這一個檔案
- **CLI entry** = 目錄中的「一筆紀錄」，描述一個 CLI 工具的基本資料（名字、怎麼裝、指令叫什麼）
- 類比：`requirements.txt` 是給自己用的購物清單；`registry.json` 是給所有人看的商品目錄

### 每個 CLI 的 metadata 欄位

| 欄位 | 用途 | threads_pipeline 對應 |
|---|---|---|
| `name` | 機器識別名 | `threads` |
| `display_name` | 給人看的名字 | `Threads` |
| `version` | 版本號 | `0.1.0` |
| `description` | 一句話說明 | "Threads API operations & post advisor" |
| `requires` | 執行前提 | `THREADS_ACCESS_TOKEN` |
| `install_cmd` | 怎麼裝 | `pip install git+...#subdirectory=...` |
| `entry_point` | 裝完後的指令名 | `cli-anything-threads` |
| `skill_md` | Agent 用法說明 md | `.../skills/SKILL.md` |
| `category` | 分類 | `social`（需新增類別） |

### 關鍵設計發現

1. **每個 harness = 一個獨立 pip 套件**
   透過 `install_cmd` 的 `git+...#subdirectory=xxx` 指向 monorepo 子目錄。
   每個子目錄自己有 `setup.py`，可獨立安裝。

2. **統一命名前綴 `cli-anything-<name>`**
   所有指令都用這個前綴避免撞名。
   例：`cli-anything-gimp`、`cli-anything-blender`、`cli-anything-wiremock`。

3. **每個 harness 都附 `SKILL.md`**
   給 Agent 讀的「怎麼用這個 CLI」說明書。
   這是 cli-anything 跟一般 CLI 最大的差別 — **Agent 是第一等使用者**。

### 對 threads_pipeline 的啟示

即使不加入 Hub，這張表就是一份「做 CLI 的檢查表」：
- [x] 有清楚的 `description`
- [x] `requires` 有沒有寫清楚（`THREADS_ACCESS_TOKEN`）
- [ ] 有沒有 `SKILL.md` 給 Agent 讀（本專案已有 `skill/threads-advisor/` 概念接近）

---

## 術語字典（給之後的自己 / 隊友）

| 術語 | 白話 | 例子 |
|---|---|---|
| **harness** | 套在另一個東西外面、讓它好用的包裝層 | `advisor.py` 是 `claude` CLI 的 harness |
| **package（套件）** | 一份可以被 `pip install` 的 Python 程式碼 | `threads_pipeline/` 加上 `pyproject.toml` 後就是 |
| **entry_point / console_scripts** | 告訴 pip「裝完後建一個短指令捷徑」的設定 | `threads-advisor=threads_pipeline.advisor:main` |
| **argparse / click / Typer** | 解析命令列參數的工具（把字串變變數） | argparse 內建、click 用裝飾器、Typer 用型別提示 |
| **decorator（裝飾器）** | 函式級別的 harness — 在函式外面再包一層 | `@click.option("--json")` |
| **stateful / stateless** | 有狀態 / 無狀態 — 是否記得之前的操作 | 你 advisor 目前全是 stateless |
| **subcommand（子命令）** | 程式底下的功能，如 `git commit` 的 commit | `threads-advisor plan` 的 plan |
| **argument / parameter（引數）** | 傳進子命令的值 | `plan "題目"` 的 "題目" |
| **`--json` / `--dry-run`** | 業界慣例 flag；格式切換 / 預演模式 | `kubectl`、`terraform` 都有 |

---

## Step 2：`mermaid/agent-harness/` — 最簡 harness 解剖

### 目錄結構

```
mermaid/agent-harness/
├── setup.py                          ← pip 打包設定
├── MERMAID.md                        ← 給人看的總覽
└── cli_anything/mermaid/             ← 真正的 Python 套件
    ├── __init__.py
    ├── __main__.py                   ← 讓 python -m 也能跑
    ├── mermaid_cli.py                ← CLI 入口（246 行）
    ├── core/                         ← 業務邏輯（diagram/export/project/session）
    ├── utils/                        ← 工具（repl_skin 等）
    └── skills/                       ← SKILL.md 給 Agent
```

### cli-anything 的隱性契約

所有 harness 都遵守同一份規範，讓 Agent「學會一個、會用全部」：

1. 指令名前綴：`cli-anything-<name>`（避免撞名）
2. 通用 flag：`--json` / `--project` / `--dry-run`
3. 支援 REPL 模式（互動）+ one-shot 模式（單次）
4. 每個 harness 自帶 `SKILL.md`
5. 目錄結構統一

---

## Step 2 的三個關鍵設計 — 逐項討論

### 設計一：`setup.py` 的 `console_scripts`（本專案會採用 `pyproject.toml`）

**做了什麼**：告訴 pip 「裝完之後幫我建一個短指令捷徑」。

**心臟程式碼**（未來本專案的 `pyproject.toml`）：
```toml
[project.scripts]
threads-advisor = "threads_pipeline.advisor:main"
```

**pip 做的事**：在 `Python313\Scripts\` 建一個 `threads-advisor.exe`，內容是：
```python
from threads_pipeline.advisor import main
main()
```

**效果**：
```bash
# 之前
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor plan "題目"

# 之後
threads-advisor plan "題目"
```

**對本專案**：✅ **必做**。這就是 Level 1 的核心。

### `setup.py` vs `pyproject.toml` 的選擇

**本專案用 `pyproject.toml`（新標準）**，理由：

| 面向 | `setup.py`（舊） | `pyproject.toml`（新） |
|---|---|---|
| 檔案性質 | Python 程式（被執行） | TOML 資料（被讀取） |
| 安全性 | 可執行惡意程式碼 | 純資料，天然安全 |
| 設定集中 | 需搭配 setup.cfg / pytest.ini / .coveragerc | 一個檔包所有工具設定 |
| 標準 | 歷史慣例 | PEP 518/621 官方標準 |
| 語法 | Python 物件 | TOML 表格（像 INI） |

**動作相同**：都是 `pip install` 來裝。差別只在 pip 讀哪個檔。

### 設計二：用 `click` vs `argparse` vs `Typer`

**cli-anything 的選擇**：click（因為子命令多、要 REPL）。

**三者對比**（同樣做 `plan` 子命令）：

| 工具 | 行數 | 特色 | 學習成本 |
|---|---|---|---|
| argparse | ~10 行 | 內建、明確、囉唆 | 低（已會） |
| click | ~6 行 | 裝飾器、優雅 | 中 |
| Typer | ~6 行 | 型別提示、最現代 | 中（多一層抽象） |

**本專案決策：保留 argparse**（Level 1 不換）

**理由**：
1. 一次只改一件事 — 這次學打包已經夠多
2. 「能動的東西不要動」— `advisor.py` 有測試、有 eval、穩定
3. 未來可**局部換**：新功能（例如 Threads API CLI）用 click，舊 advisor 繼續 argparse 共存

**未來若決定換（Level 2+）的觸發條件**：
- 子命令爆炸（例如 `threads posts search` 這種巢狀）
- 想做 REPL 模式
- 想用 click 的 `prompt-toolkit` 整合

### 設計三：`Session` + 三個通用 flag

設計三其實是**四個小設計**綁在一起：

| 元素 | 角色 | 本專案是否採用 |
|---|---|---|
| `Session` | 狀態管理（跨命令） | ❌ **不採用**（Level 3 才需要） |
| `--json` flag | 輸出格式切換（人 vs 機器） | ✅ **補齊**（review/analyze/list-frameworks） |
| `--project` flag | state 檔選擇 | ❌ 已用位置參數等效實現 |
| `--dry-run` flag | 預演模式（假執行） | ✅ **局部採用**（`plan` 加，其他免） |

**逐項說明**：

**① `Session`（不採用）** — advisor 的三個子命令都是 stateless 一次性任務，不需要跨命令保留 context。未來若做多輪互動編輯 draft 才需要。

**② `--json`（補齊）** — `plan` 已有，補到 `review` / `analyze` / `list-frameworks`。成本很低，每個命令約 10–20 行。理由：Agent 解析 JSON 比解析人讀格式輕鬆太多。

**③ `--project`（不採用）** — 你 `advisor review drafts/xxx.txt` 已經等效實現了 project 選擇，只是用位置參數。名字不重要，功能到位就好。

**④ `--dry-run`（局部採用）** — 只給 `plan` 加，因為 `plan --auto --overwrite` 會蓋掉 drafts/ 檔。`review` / `analyze` 沒寫檔副作用，不需要。**未來做 Threads API publish 時，`--dry-run` 強制必備**（發錯文無法撤回）。

---

## 與 `python-pro` skill 的對比

`~/.claude/skills/python-pro/` 是一份通用 Python 最佳實踐 skill，但**偏向 Web 後端（FastAPI + Pydantic + Docker）情境**。做 CLI 工具時需要篩選採用。

### ✅ 呼應本專案決策

- Python 3.12+ / pyproject.toml / ruff lint / pytest / type hints / 環境變數配置

### ⚠️ python-pro 推薦但**不適用於 CLI 情境**

| python-pro 推薦 | 為何不適用 |
|---|---|
| FastAPI | 我們做 CLI 不是 Web API |
| Pydantic 驗證所有輸入 | argparse / click 已做驗證；Pydantic 在 CLI 是 overkill |
| Docker 容器化 | 個人 CLI 不需要；`pip install -e .` 足夠 |
| async / asyncio | 我們是 subprocess + SQL，非 I/O bound |
| `uv` 取代 pip | pip 已夠用，「能動的不要動」 |
| 90% 測試覆蓋率 | 理想值，非硬性門檻 |

### ⚠️ python-pro 沒涵蓋（CLI 情境的盲點）

- `[project.scripts]` / `entry_points` 打包 CLI
- argparse vs click vs Typer 選擇
- `--json` / `--dry-run` 慣例 flag
- CLI error code 規範（`exit(1)` 等）
- `--help` 文字設計

### 使用原則

> **skill 是工具，不是聖旨。** python-pro 的「Must-Follow」只在 Web 後端情境為真。
> CLI 特定設計交給本研究文檔 + cli-anything 參考 + 自主判斷。

篩選後可採用：
- `[tool.ruff]` / `[tool.pytest.ini_options]` 放進 pyproject.toml
- type hints 逐步補齊
- 避免全域狀態原則（advisor.py 的 `_session` 模式是 cli-anything 的刻意設計，不衝突）

---

## Step 3：`cli-hub/` 本體 — Hub 自己怎麼打包

### 核心角色：cli-anything 生態的「套件管理器」

| 生態 | 管理器 |
|---|---|
| Python 套件（PyPI） | pip |
| Node.js 套件（npm registry） | npm |
| **cli-anything 生態** | **cli-hub** |

提供的指令：`cli-hub list / search / install / uninstall / update / info`。

### 內部運作

```
使用者打 cli-hub install gimp
    ↓
讀 registry.json → 找 gimp entry → 取 install_cmd
    ↓
呼叫 pip 執行 install_cmd
    ↓
cli-anything-gimp 指令可用
```

**關鍵**：Hub 不自己做 install，呼叫 pip。它只是「查目錄 + 轉接頭」。

### 職責切分（479 行總計）

```
cli_hub/
├── cli.py         ← 指令解析 + 輸出（168 行）
├── registry.py    ← 查 registry.json（72 行）
├── installer.py   ← 呼叫 pip install/uninstall（107 行）
└── analytics.py   ← 匿名使用量統計（129 行）
```

`setup.py` 關鍵配置：
```python
name="cli-anything-hub",
install_requires=["click>=8.0", "requests>=2.28"],
entry_points={"console_scripts": ["cli-hub=cli_hub.cli:main"]},
```

**Hub 本身也是一個 harness，吃自己的狗糧**。

### 對 threads_pipeline 的啟示

1. **套件可以很薄** — Hub 才 479 行，不用擔心 CLI 化會很複雜
2. **不需要自建 Hub** — threads_pipeline 是「生態裡的商品」，不是「生態管理器」
3. **關注點分離可抄** — 未來做 Threads API CLI 時：
   - `cli.py` ← 指令解析
   - `threads_client.py` ← API client（已有）
   - `output.py` ← JSON / 人讀格式化

---

## Step 4：`CONTRIBUTING.md` — 加入 cli-anything 生態的兩條路徑

### 路徑 A：塞進 monorepo（不推薦給本專案）

code 搬進 HKUDS/CLI-Anything 的子目錄，受他們 PR 流程管。

### 路徑 B：自己 repo + 只交 registry PR（本專案唯一合理選擇）

```
azuma520/threads_pipeline/       ← 本專案（不動）
     ↓ 對應到
HKUDS/CLI-Anything/registry.json ← 只 PR 改這一個檔
     加一筆 entry 指向本 repo
```

### 路徑 B 的要求（11 個欄位，影響現在決策的有 3 個）

| 欄位 | 意義 | 本專案怎麼做 |
|---|---|---|
| `install_cmd` | 能被 `pip install` | → 要寫 `pyproject.toml` |
| `entry_point` | 有 CLI 指令 | → 要寫 `[project.scripts]` |
| `skill_md` | 給 Agent 讀的說明 | → 補一份 `SKILL.md`（已有 `skill/threads-advisor/` 基礎） |

### 本專案的決策原則

1. **Level 1 打包時順便符合 Hub 介面**（不是為了加入，是為了保留未來選項）
2. **命名中立** — 用 `threads-advisor` / `threads` 而非 `cli-anything-threads`，避免被綁架。未來加入 Hub 時可在 `pyproject.toml` 加別名
3. **發佈 PyPI 不是 Level 1 的事** — `install_cmd` 可用 `pip install git+https://...`，不必發 PyPI

### 觀察：它在「定義標準」而非「邀請貢獻」

CONTRIBUTING.md 讀起來像規範文件。**Hub 不挑內容、只挑格式** — 符合 11 個 registry 欄位 + 有 SKILL.md + 能 pip install 就能上架。**最小承諾、最大包容**的生態設計哲學。

---

## Step 4：`CONTRIBUTING.md` — 新 harness 的 spec 範本

> 待補

---

## 整合結論

### Q1：打包路線？
**獨立 pip 套件**（不塞 monorepo、不自建 Hub）。
- 用 `pyproject.toml` + `[project.scripts]` 做 Level 1 打包
- 未來若決定加入 cli-anything Hub，走 CONTRIBUTING 路徑 B（只交 registry PR，repo 保留在自己名下）

### Q2：哪些元件值得 CLI 化？（尚待最終決策）

三個候選範圍（對應 brainstorming Q1）：
- **A：只做 advisor**（plan / review / analyze / list-frameworks）← 最保守
- **D：advisor + 唯讀 Threads API**（posts search / insights latest / account info）← 推薦
- **E：D + 發文 API**（publish / reply）← 等 Advanced Access 核准 + `--dry-run` 做好

決策延後到 brainstorming 階段敲定。

### Q3：是否加 state / undo / REPL？

**Level 1 全部不做**。理由：
- advisor 子命令皆 stateless，`Session` 無使用情境
- undo/redo 需搭配 state 系統，不獨立做
- REPL 需 click + prompt-toolkit 生態，且目前無使用需求

未來若擴展到多輪 draft 編輯（Level 3）再評估。

### Q4：是否附 `SKILL.md`？

**建議補**（但非 Level 1 必做）。
- 專案已有 `skill/threads-advisor/` 相關檔，概念接近
- 補一份標準格式的 `SKILL.md` 放在 `cli_anything/threads/skills/SKILL.md`，成本不高
- 好處：未來加入 Hub 時 `skill_md` 欄位有東西可填

### Level 1 實作清單（CLI 化最小集）

1. 建立 `pyproject.toml`
   - `[build-system]` / `[project]` / `[project.scripts]`
   - `threads-advisor` 指向 `threads_pipeline.advisor:main`
   - （視 Q2 結論決定是否加 `threads-pipeline` / `threads`）
2. `pip install -e .` 本機驗證
3. 測試 `threads-advisor plan "題目"` 能取代原本 `python -m threads_pipeline.advisor plan "題目"`
4. 更新 CLAUDE.md 的 Commands 區塊（從 `python -m` 改成短指令）
5. （可選）補齊 `--json` flag 到 review / analyze / list-frameworks
6. （可選）給 `plan` 加 `--dry-run`

### 刻意排除的項目（避免範圍蔓延）

- ❌ 改 argparse → click
- ❌ 改 pip → uv
- ❌ 加 Pydantic / FastAPI / Docker（python-pro 推薦但與 CLI 情境不符）
- ❌ 發佈到 PyPI
- ❌ 撰寫 SKILL.md（未來若加入 Hub 再補）
- ❌ Session / undo / REPL
