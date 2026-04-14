# advisor plan — 串文骨架生成器 設計文件

**日期**：2026-04-14
**狀態**：草稿（待 codex-architect + tech-spec-reviewer 審查）
**相關**：補 `advisor analyze` 與 `advisor review` 之間缺的「plan.md 生成」環節

---

## 1. 背景與動機

### 現況

`advisor` 模組有兩個子指令：

- `advisor analyze` — 讀 SQLite insights 產數據分析報告
- `advisor review` — 讀 `drafts/{topic}.plan.md` + 草稿，用 Codex CLI 做六維度審查

`review` 的設計已預期會吃一份 `plan.md`（包含受眾、結構指引），但**目前 plan.md 需人工撰寫**。使用者主訴是「有想法但不知道怎麼組織成串文」，這個手寫步驟因此成為瓶頸。

### 外部參考

專案內 `references/copywriting-frameworks.md` 已收錄「爆款文案腳本 16+1 結構」（魏育平課程）。每個框架有公式與適用場景，並附「選擇指南」將情境對映到推薦框架。這份文件尚未被任何程式利用。

### 範圍限制

- Threads Advanced Access 尚未核准，**不可依賴跨帳號搜尋**或外部趨勢抓取
- 可用資料源：使用者自有 SQLite（post/account insights、`full_text`）、Threads API 自家帳號端點、`references/` 靜態文件

---

## 2. 目標與非目標

### 目標

1. 新增 `advisor plan "題目"` 指令，產出 `drafts/{slug}.plan.md`，可直接接上既有 `advisor review`
2. 產出品質：骨架符合 16+1 框架之一的公式、語氣貼近使用者歷史高互動貼文
3. 支援兩種格式：Threads 串文（7–10 條，預設）／單篇長文（≤500 字，`--format single`）
4. Agent-friendly：所有互動皆有非互動旗標等價；stdin 非 tty 時自動 headless

### 非目標（YAGNI）

- 自動發文（另一個子系統）
- 視覺/首圖設計建議（純文字 LLM 對視覺建議價值低）
- 跨帳號趨勢研究（需 Advanced Access，暫緩）
- plan.md 的後續成稿（使用者自己填，走 `review` 審查）

---

## 3. 架構

### 模組分工

```
threads_pipeline/
├── advisor.py              # +新增 plan、list-frameworks 子 parser 與 _cmd_plan()
├── planner.py              # +新模組：框架選擇、prompt 組裝、LLM 呼叫、plan.md 渲染
├── templates/
│   └── plan_output.md.j2   # +新模板：最終 plan.md 格式
├── references/
│   └── copywriting-frameworks.md   # 既有，不動
├── db_helpers.py                   # 既有 get_top_posts 直接用
└── tests/
    ├── test_planner.py             # +單元 + 整合測試（mock LLM）
    └── evals/
        └── test_plan_quality.py    # +LLM-as-judge eval（subagent）
```

**`advisor.py` 只負責 CLI 與協調**；所有生成邏輯搬進 `planner.py`，保持單一職責（`advisor.py` 已 ~400 行）。

### 資料流

```
                    ┌─ references/copywriting-frameworks.md
[Stage 1]           │
題目 ─────────────→ │  claude -p --model haiku ──→ JSON
                    │  （挑 3 個框架 + 理由）      {suggestions: [...]}
                    └────────────────────────────────────────┘
                                    ↓
                        人工選 / --framework / --auto
                                    ↓
                    ┌─ 單一框架章節（從 md 切出）
[Stage 2]           ├─ SQLite top 5 貼文 full_text
題目 + 框架 + 格式 →│  claude -p --model sonnet ──→ Markdown 骨架
                    └────────────────────────────────────────┘
                                    ↓
                            drafts/{slug}.plan.md
```

### 為什麼兩階段 + 不同模型

- **Stage 1（選框架）**：分類判斷任務，haiku 勝任且成本低
- **Stage 2（生骨架）**：創意 + 風格對齊，haiku 產出易糊；預設 sonnet，可 `--model` 覆寫
- 兩階段讓選框架透明化，使用者能在低成本決策點介入

---

## 4. CLI 介面

### 主指令

```bash
advisor plan "題目"                            # 兩階段互動（預設）
advisor plan "題目" --auto                     # 略過互動，用 LLM 第一推薦
advisor plan "題目" --framework 11             # 強制指定（編號或名稱）
advisor plan "題目" --framework 逆襲引流
advisor plan --topic-file drafts/ideas/x.md   # 長題目用檔案
advisor plan "題目" --format single           # 預設 thread
advisor plan "題目" --style-posts 3           # 風格範本條數，預設 5
advisor plan "題目" --model haiku             # 覆寫 Stage 2 模型，預設 sonnet
advisor plan "題目" --suggest-only --json     # 只回建議、不生檔；吐 JSON 到 stdout
advisor plan "題目" --auto --overwrite        # 完全 headless
advisor plan "題目" --no-overwrite            # 檔案已存在即報錯退出
```

### 輔助指令

```bash
advisor list-frameworks         # 列出 17 個框架的編號、名稱、公式、適用場景
advisor list-frameworks --json  # agent 友善
```

### 互動流程（無旗標）

```
$ advisor plan "我學 Claude Code 一個月的心得"

✓ 讀取分析摘要：output/advisor/analysis_2026-04-14.json
✓ 讀取風格範本：SQLite top 5 貼文
正在分析題目適合的結構（claude -p haiku）...

LLM 建議 3 個候選框架：

  [1] 11 逆襲引流 ★推薦
      公式：積極結果 → 獲得感 → 方案 → 互動結尾
      為什麼：這是「一個月成果分享」，逆襲引流擅長把過程講得有獲得感

  [2] 16 教知識經典
      公式：問題描述 → 問題拆解 → 答案描述 → 答案拆解
      為什麼：如果想把學習方法講深，結構最扎實

  [3] 14 感性觀點
      公式：事實 → 感受 → 發現問題 → 結論 → 故事 → 總結
      為什麼：如果想講心路歷程勝過實用方法

請選擇 [1/2/3 / a=全部列出 / q=取消]: _
```

- `1/2/3` → 用該框架進 Stage 2
- `a` → 列出全部 17 個框架再問一次
- `q` → 退出不產檔（exit code 2）

### Agent-friendly 約定

| 項目 | 行為 |
|------|------|
| 狀態訊息 | stderr |
| 最終結果路徑 / `--json` 結果 | stdout |
| stdin 非 tty 且未給 `--auto` / `--framework` | 自動等同 `--auto`，stderr 警告 |
| 退出碼 | `0` 成功、`1` 一般錯誤、`2` 使用者取消、`3` LLM 失敗、`4` 檔案已存在且 `--no-overwrite` |

### Slug 規則

- 取題目前 20 個字元（以 Python len 計，中文算 1）
- 空白轉 `-`，移除 `/\:*?"<>|` 等檔名不合法字元
- 結果若為空（全特殊字元）→ 加 `plan-{YYYYMMDD-HHMM}` 時間戳
- slug 本身小寫（但保留中文）

---

## 5. Prompt 設計

### Stage 1（選框架）

```
你是 Threads 內容結構顧問。以下是 16+1 個文案框架：

{完整貼上 copywriting-frameworks.md}

使用者題目：{topic}

請挑出最適合這個題目的 3 個框架，依匹配度排序。
輸出純 JSON（不要 markdown code fence）：

{
  "suggestions": [
    {"framework": 11, "name": "逆襲引流", "reason": "一句話理由"},
    ...
  ]
}
```

**輸出解析**：`json.loads(stdout)`；失敗 → exit code 3 並 fallback 改用 framework 15（通用類），stderr 警告。

### Stage 2（生骨架）

```
你是 Threads 串文結構專家。任務：把題目套用指定框架，產出可直接填內容的骨架。

## 題目
{topic}

## 指定框架
{從 md 切出的單一框架章節，含公式與適用場景}

## 風格範本（使用者過去高互動貼文，模仿語氣與句型，不要抄內容）
[第 1 篇] 互動率 X%
{full_text}
---
...

## 輸出格式要求
- Format: {thread | single}
- Thread: 7-10 條，每條 300-500 字；主貼定調、後續遞進
- Single: 1 條 ≤500 字，壓縮完整結構

## 輸出 Markdown 結構（照這個格式輸出）

# {題目}

- 框架：{編號} {名稱}
- 格式：{thread | single}
- 預估字數：{總字數}

## 骨架

### 主貼（P1）
- 【鉤子類型】：
- 【字數建議】：
- 【內容方向】：2-3 句指引，**不是成稿**
- 【情緒】：

### P2
...

## 互動設計
- 結尾 CTA 類型（互動式/夥伴式/Slogan/反轉式）：
- 可加的互動元素：

## 風險提示
LLM 自評骨架可能的弱點 1-2 點。
```

**核心設計**：產出是**骨架而非成稿**。每條貼文給內容方向，使用者自己填——維持使用者創作主體性，也符合「分享自己」的內容哲學。

### Token 預算估計

- Stage 1：frameworks md（~2k 字） + 題目 ≈ 2.5k input tokens
- Stage 2：單一框架 + top 5 `full_text`（~2.5k 字） + 題目 ≈ 3k input / 1.5k output
- 一次 `plan` 合計約 5k input，成本預估 <$0.02

---

## 6. 錯誤處理

| 情境 | 行為 | 退出碼 |
|------|------|--------|
| 題目為空 | stderr 提示，需 `--topic-file` 或引號題目 | 1 |
| SQLite 找不到 | stderr 提示「請先跑 pipeline」 | 1 |
| top posts 不足 5 篇 | 有幾篇用幾篇，警告；0 篇 → 略過風格範本繼續 | 0 |
| `claude -p` 超時（60s） | retry 1 次，再失敗回報 | 3 |
| Stage 1 JSON 解析失敗 | fallback framework 15 + stderr 警告 | 0 |
| `--framework` 指定不存在 | 列出合法選項後退出 | 1 |
| `drafts/{slug}.plan.md` 已存在 | 無旗標 → 互動問；`--overwrite` → 蓋；`--no-overwrite` → 退出 | 4 |
| 互動模式選 `q` | stderr「已取消」 | 2 |
| stdin 非 tty 但沒給 `--auto` / `--framework` | 自動等同 `--auto`，stderr 警告 | 0 |

---

## 7. 測試策略

### Layer 1 — 傳統單元測試 (`tests/test_planner.py`)

不呼叫真 LLM，測管線正確性：

- `parse_suggestions_json()` — 合法 / 不合法 / 欄位缺失 / 多餘欄位
- `extract_framework_section(md, framework_id)` — 編號查 / 名稱查 / 不存在
- `slugify(topic)` — 中英混 / 純中文 / 特殊字元 / 超長 / 空白
- `build_stage1_prompt()` / `build_stage2_prompt()` — 輸入組成正確字串
- `render_plan_md()` — Jinja2 渲染正確

### Layer 2 — 整合測試（mock `subprocess.run`）

- 完整 `plan "題目" --auto`：mock Stage 1 + Stage 2 → 驗證最終 plan.md 內容
- JSON 解析失敗 → fallback 15 路徑
- `--overwrite` / `--no-overwrite` 行為
- stdin 非 tty → 自動走 auto

### Layer 3 — LLM-as-judge Eval (`tests/evals/test_plan_quality.py`)

**核心洞察**：這是 LLM 生成工具，單元測試 100% 通過不代表產出可用。用 subagent 對實際產出做品質評分。

- 準備 3-5 個 golden 題目（涵蓋教學、經驗分享、觀點表達三類）
- 對每個題目執行真實 `advisor plan --auto`
- 用 `codex-cli-review` 或自寫評審 subagent，帶下列 rubric 打分（1-5）：
  1. **框架公式對齊度**：骨架是否真的符合所選框架的公式順序？
  2. **風格一致性**：語氣、句型是否貼近 top 5 範本？
  3. **可執行性**：「內容方向」是否具體到使用者能直接填內容？
  4. **格式正確性**：thread 7-10 條 / single ≤500 字規則是否遵守？
  5. **避免 AI 味**：有沒有誇大象徵、-ing 膚淺分析、破折號過度等 AI 特徵？
- 任一項 <3 → eval 失敗
- 不每 PR 跑，作為人工 release gate

### 不測

- 真實 `claude -p` 每 PR 呼叫（成本、不穩定）

---

## 8. 風險與未決事項

### 風險

1. **Stage 2 用 sonnet 成本**：若使用量大，考慮改預設 haiku。先上線觀察。
2. **風格範本污染**：早期 top posts 數少或品質不一時，模仿可能學到壞習慣。緩解：`--style-posts` 可調 0 關閉。
3. **Slug 碰撞**：同題目第二次跑會觸發覆寫決策。可接受。
4. **16+1 框架描述不夠豐富**：目前「適用場景」一句話，LLM 或人挑選時資訊可能不夠。緩解：先跑看看，若 eval Layer 3 發現框架挑錯率高，再補描述。

### 未決事項

- [ ] Stage 2 預設是否真用 sonnet？（本設計假定 yes，待審查意見）
- [ ] `--style-posts` 預設 5 是否合理？（早期數據少時可能過多）
- [ ] `list-frameworks` 是否值得獨立子指令？（或合併到 `plan --list`）

---

## 9. 落地計畫（高階）

1. 實作 `planner.py` 骨幹（slug、frameworks 切章節、prompt 組裝）
2. 實作 `advisor plan` 子 parser + `_cmd_plan()`
3. `plan_output.md.j2` 模板
4. `list-frameworks` 子指令
5. Layer 1 + Layer 2 測試
6. 手動 smoke test 3 個題目
7. Layer 3 eval rubric + subagent 腳本
8. 補文件：CLAUDE.md 加 `advisor plan` 使用範例

詳細實作步驟由後續 `writing-plans` 階段產出。

---

## 10. 審查記錄

- [ ] codex-architect 審查（待執行）
- [ ] tech-spec-reviewer 審查（待執行）
- [ ] 使用者最終審查
