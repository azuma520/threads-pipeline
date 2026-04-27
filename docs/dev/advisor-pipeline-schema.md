# advisor Path A Pipeline — Artifact Schema + Stage Gate

> 為 advisor 寫貼文流程提供工程化契約。每個 Stage 的輸出必須符合 schema，每個 Gate 必須通過 checklist 才能進下一 Stage。
>
> **建立背景**：0424 18:07 session AI 違反 skill 紀律 3 次（edgy sharpness / self-deprecation / 跳步驟反序讀 reference），根因是 pipeline 缺工程化（無 stage gate / 無 lint / 無依賴檢查）。本文檔補 A 層（artifact schema）+ B 層（stage gate）作為純文字契約。
>
> **適用範圍**：`SKILL.md` 路徑 A（Plan — 寫新串文）。路徑 B/C/D 不在本文檔。
>
> **檔名規範**：所有 stage artifact 寫到 `drafts/<slug>.<stage>.md`。`<slug>` 跨 stage 一致，由 Stage 0 angle.md 決定。

---

## Pipeline Iron Law（cross-cutting，凌駕全文件）

```
NO STAGE PROGRESSION WITHOUT FRESH GATE EVIDENCE.
```

If you haven't checked the Gate checklist in **this message**, you cannot claim Stage N is complete. **Spirit over letter** — finding a loophole in the wording is still a violation.

### Gate Function（每進下一 Stage 前必跑）

1. **IDENTIFY**：上一 Stage 的 Gate 是哪一條（Gate N→N+1）？
2. **CHECK**：Gate checklist 全部 checkbox 是否在「本訊息」中逐條跑過？
3. **READ**：每個 checkbox 對應的 artifact 欄位是否真的存在於檔案（不是 stale memory）？
4. **VERIFY**：User align 是否已在「本 session」明確發生（不是「之前 align 過」）？
5. **ANNOUNCE**：明確聲明 Gate 結果（PASS / FAIL + 缺什麼）

### Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Stage 1 done | framework.md 含 chosen_framework + chosen_reason 非空 + user 本 session 確認 | 「user 0424 選過 PREP」 |
| Stage 2 done | plan.md 6 章節齊 + 字數 ≤ 3500 + user align | 「骨架方向已 align」 |
| Stage 5 reference 讀過 | `references_read_in_order: true` 寫進 frontmatter + 三檔讀於本 session | 「我有印象讀過」 |
| Gate PASS | 本訊息逐條跑 checklist + 對 artifact 欄位實檢 | 「應該 OK」「差不多」 |

### Rationalization Prevention

| 藉口 | 現實 |
|------|------|
| 「user 之前 align 過了」 | 重新驗 — 之前的 align 是不同 stage 不同 artifact |
| 「我記得內容差不多」 | 記憶 ≠ artifact，重看檔案 |
| 「先進下個 stage 之後補」 | 永遠不會補；現在不過 Gate = 永遠不過 |
| 「auto mode 要快」 | auto mode 不豁免 Iron Law |
| 「mimic 不是正規 CLI 不算」 | mimic 仍要過 Gate；mimic 不是免責標籤 |
| 「這條 checkbox 不重要」 | checkbox 不分輕重，全勾才 PASS |

### Red Flags — STOP

- 任何 Stage 完成宣告未列具體 evidence
- 「應該」「大概」「我印象中」這類字眼出現在 Gate 評估
- Skip 一個 checkbox 想「事後補」
- 用 user 的 align 替代 artifact 存在
- 把不同 Stage 的 align 拿來 cross-reference

---

## Stage Entry Template

每進入一個 Stage，**第一個訊息必須以下列格式 announce**（不可省略；省略 = 跳 Stage = Iron Law violation）：

```
I'm entering Stage N — <stage name>.
- Upstream artifact: <path to upstream artifact>
- Upstream Gate status: <PASS / FAIL — 評估結果摘要>
- This stage produces: <path to this stage's artifact>
- Schema requirements: <列出本 stage 所有必填欄位>
- Required references to read (if any): <列出 + 順序>
```

並在本 stage 產出的 artifact frontmatter 加：

```yaml
stage_entry_announced: true
upstream_gate_passed: true
references_read_in_order:  # Stage 5 only — 證據欄位
  - philosophy
  - content-structure
  - voice-patterns
```

未做 announce 視為「跳 Stage」。`stage_entry_announced` 欄位是強制 audit trail，不可省略。

---

## Part A：每 Stage Artifact Schema

### Stage 0 — angle.md（已由 `threads-angle-gate` skill 實作）

必填欄位：

- `topic`：題目（一句話）
- `sharpness`：銳利切入點（不是 surface description）
- `reader_value`：讀者為什麼會想看
- `source`：`co_created` / `observed` / `quoted` 三選一
- `source_quotes`：使用者原話佐證（避免 AI 投射）

範例：`drafts/ai-tool-reflection-rhythm.angle.md`

**Plan Failures（angle.md 含以下任一即 Gate 0→1 FAIL）：**
- `topic` 含 「TBD」「待定」
- `sharpness` 為 surface description（重述題目而非銳利切入）
- `reader_value` 寫「分享經驗」「給大家參考」這類空話
- `source` 不在 {co_created, observed, quoted}
- `source_quotes` 為空（co_created 必須有 user 原話）
- 含 `（空白）` 或佔位文字

---

### Stage 1 — framework.md

必填欄位：

- `considered_frameworks`：3 個框架（不少不多），每個含
  - `id`：編號（01–17）
  - `name`：框架名
  - `formula`：公式
  - `why_fit`：為什麼適合本題目
- `chosen_framework`：使用者選定的（單一）
  - `id` / `name`
  - `chosen_reason`：使用者選擇理由（避免「順手選」記錄為空）

**對應 CLI**：`advisor plan --suggest-only --json` 產 JSON，但目前**沒寫成檔**。新規範：選完框架要寫到 `drafts/<slug>.framework.md`（保留 decision trace）。

**Plan Failures（framework.md 含以下任一即 Gate 1→2 FAIL）：**
- `considered_frameworks` 數量 ≠ 3（少於 3 視為 reasoning 不足；多於 3 視為未收斂）
- 任一 considered framework 的 `why_fit` 為空或寫「適合」「OK」「不錯」
- `chosen_framework.id` 不在 16+1 清單（編造視為違規）
- `chosen_reason` 為空 或 寫「順手選」「random」「都可以」
- `chosen_framework` 仍為 `?` 或空（user 未選定卻聲稱 Gate PASS）

---

### Stage 2 — plan.md

必填章節（依序）：

1. **頭部**：題目 / 框架編號+名稱 / 格式（thread / single） / 預估總字數
2. **目標受眾**：誰會想讀（1–2 句具體） / 痛點動機
3. **起承轉合 mapping**：哪段對應起承轉合哪部分（顯式化）
4. **骨架**：每條 post 含
   - 【鉤子類型】
   - 【字數建議】
   - 【內容方向】（2–3 句指引，**不是成稿**）
   - 【情緒】
5. **互動設計**：結尾 CTA 類型（互動式 / 夥伴式 / Slogan / 反轉式） + 可加的互動元素
6. **風險提示**：LLM 自評骨架可能弱點 1–2 點

**字數約束**：總長 ≤ 3500 字元

**對應 CLI**：`advisor plan --framework N --overwrite`（feat/advisor-plan branch，未 merge）。CLI 不可用時 mimic，但必須符合本 schema。

**Plan Failures（plan.md 含以下任一即 Gate 2→3 FAIL）：**
- 缺任一必填章節（頭部 / 受眾 / 起承轉合 mapping / 骨架 / 互動設計 / 風險提示）
- 骨架某條缺【鉤子類型】或【字數建議】或【內容方向】或【情緒】
- 內容方向寫成「成稿」（schema 規定 2-3 句指引，不是文字稿）
- 含「（空白）」「（之後填）」「TBD」「待寫」
- 起承轉合 mapping 隱在骨架內未顯式列出
- 總字數 > 3500

---

### Stage 3 — algo.md（NEW）

必填欄位：

- 每條 post 對應至少 1 個演算法機制：
  - `post_position`：第幾條（P1 / P2 ⋯）
  - `mechanism`：機制名（**必須來自 threads-algorithm-skill 的 26 機制清單，不准編造**）
  - `why_applies`：為什麼這條適用此機制
  - `risk`：可能的反作用 / 邊界
- 整體：
  - `dominant_mechanisms`：本篇主訴求的 2–3 個機制
  - `avoid_mechanisms`：本篇刻意避開的機制（如 Low Signal）

**Plan Failures（algo.md 含以下任一即 Gate 3→4 FAIL）：**
- 任一 post 沒對應 mechanism
- mechanism 名稱**未引用 threads-algorithm-skill 26 機制清單原文**（編造視為違規）
- `why_applies` 為空或寫「相關」「適合」這類空話
- `risk` 為空（每個機制都有 trade-off，必須列）
- `dominant_mechanisms` 與每條 post mechanism 不相干（不一致）

---

### Stage 4 — interaction.md（NEW）

必填欄位：

- `chosen_types`：從 5 類型選 2–3 個（**不接受 1 個或 4 個以上**）
  - `type`：開放式問題 / 爭議觀點 / 個人經驗邀請 / 投票選擇題 / 標記朋友
  - `post_position`：放在哪一條
  - `why_this_post`：為什麼這條最適合放這個互動
  - `example_phrasing`：示範句（不是成稿，是 hint）

**Plan Failures（interaction.md 含以下任一即 Gate 4→5 FAIL）：**
- `chosen_types` 數量 ∉ {2, 3}（1 個過少；4+ 過密）
- 任一 chosen type 的 `post_position` 與 plan.md 骨架不對應
- `why_this_post` 為空或寫「適合」「自然」這類空話
- `example_phrasing` 為空（必須給 hint，否則 Stage 5 無從寫起）
- 5 類型清單外的自創類型（必須來自 schema 規定的 5 類型）

---

### Stage 5 — draft.md（NEW）

必填欄位：

- `posts`：N 條完整文字
  - `position`：P1 / P2 ⋯
  - `text`：完整文字
  - `char_count`：字數
- `references_read_in_order`：true（本欄位**必須有**，證明依序讀過 philosophy → content → voice）
- `voice_self_check_results`：見 Part C 的 checklist 通過記錄

**字數約束**：每條 80–300 字 / 整串 ≤ 2000 字（爆款參考線）

**Plan Failures（draft.md 含以下任一即 Gate 5→6 FAIL）：**
- `references_read_in_order` 欄位缺 或 false
- 任一 post `text` 為空 或 含「（待寫）」
- 任一 post 字數 ∉ [80, 300]
- 整串字數 > 2000
- 含結構名（「PREP」「鉤子」「骨架」⋯）出現在正文 — Part C 唯一 hard lint
- **寫作品味問題**（贅詞 / 評論體 / 教訓體 / self-deprecation / AI 整齊感）→ 不是 Plan Failure，由 user 在 Stage 5/6 用編輯眼光審；Part C 寫作技巧筆記是 AI 寫稿時的參考而非 hard rule

---

### Stage 6 — review.md（已由 `advisor review` CLI 實作）

由 CLI 產出。新增 user 採納記錄：

- `cli_suggestions`：CLI 原始建議
- `user_accepted`：使用者決定採納哪幾條
- `applied_to_draft`：採納的修改已套到 draft，true / false

**Plan Failures（review.md 含以下任一即 Gate 6→7 FAIL）：**
- `cli_suggestions` 為空（CLI 沒跑或 output 沒貼）
- `user_accepted` 未明確列出哪幾條
- `applied_to_draft: true` 但 draft.md 未實際更新
- 跳過 `advisor review` CLI 直接宣告 review 完成

---

### Stage 7 — published.md

發文後產出：

- `post_id`：Threads 回傳的 post_id
- `published_at`：發文時間
- `dry_run_confirmed_by_user`：true（dry-run 預覽過再發）

**Plan Failures（published.md 含以下任一即發文失敗）：**
- 未跑 dry-run 直接 `--confirm --yes`
- `dry_run_confirmed_by_user: false` 卻已 publish
- `post_id` 為空（API 失敗未確認）

---

## Part B：Stage Gate Checklist

每個 Gate 問三件事：
1. **Artifact 是否存在且符合 schema？**
2. **使用者是否 align？**（不是 AI 自判）
3. **下一 Stage 的前置依賴是否齊？**

### Gate 0 → 1

- [ ] `*.angle.md` 存在
- [ ] `sharpness` 非空
- [ ] `reader_value` 非空
- [ ] `source` ∈ {co_created, observed, quoted}
- [ ] **User align**：「這個角度對嗎」

**REQUIRED NEXT STEP**：進 Stage 1 前，本 Gate 全部 checkbox 必勾。任一未勾 = Gate FAIL = **不得**進 Stage 1。藉口（「差不多」「之後補」）= 違規，重跑 Gate，不重新進下一 Stage。

### Gate 1 → 2

- [ ] `*.framework.md` 存在
- [ ] 列出 3 個 considered framework
- [ ] `chosen_framework.id` ∈ 16+1 清單
- [ ] `chosen_reason` 非空（不接受「順手選」）
- [ ] **User align**：「這個框架對嗎」

**REQUIRED NEXT STEP**：進 Stage 2 前，本 Gate 全部 checkbox 必勾。任一未勾 = Gate FAIL = **不得**進 Stage 2。藉口（「差不多」「之後補」）= 違規，重跑 Gate，不重新進下一 Stage。

### Gate 2 → 3

- [ ] `*.plan.md` 存在
- [ ] 6 個必填章節都在（頭部 / 受眾 / 起承轉合 mapping / 骨架 / 互動 / 風險）
- [ ] 骨架每條都含【鉤子類型】【字數建議】【內容方向】【情緒】
- [ ] **起承轉合 mapping 顯式列出**（不是隱在骨架裡）
- [ ] 總字數 ≤ 3500
- [ ] **User align**：「骨架結構對嗎，有沒有要重做」

**REQUIRED NEXT STEP**：進 Stage 3 前，本 Gate 全部 checkbox 必勾。任一未勾 = Gate FAIL = **不得**進 Stage 3。藉口（「差不多」「之後補」）= 違規，重跑 Gate，不重新進下一 Stage。

### Gate 3 → 4

- [ ] `*.algo.md` 存在
- [ ] 每條 post 對應 ≥ 1 個機制
- [ ] 機制名**全部來自 threads-algorithm-skill 26 機制清單**（編造視為 fail）
- [ ] **User align**：「演算法解讀對嗎」

**REQUIRED NEXT STEP**：進 Stage 4 前，本 Gate 全部 checkbox 必勾。任一未勾 = Gate FAIL = **不得**進 Stage 4。藉口（「差不多」「之後補」）= 違規，重跑 Gate，不重新進下一 Stage。

### Gate 4 → 5

- [ ] `*.interaction.md` 存在
- [ ] `chosen_types` 數量 ∈ {2, 3}
- [ ] 每個都有 `post_position` 標明放在哪條
- [ ] **User align**：「互動設計對嗎」

**REQUIRED NEXT STEP**：進 Stage 5 前，本 Gate 全部 checkbox 必勾。任一未勾 = Gate FAIL = **不得**進 Stage 5。**特別注意**：Stage 5 進入前必須在本訊息依序讀完 `references/writing-philosophy.md` → `references/content-structure.md` → `references/voice-patterns.md` 三份檔，並在 draft.md frontmatter 寫 `references_read_in_order: true`。順序錯 = Gate FAIL。

### Gate 5 → 6（最嚴格的 gate）

- [ ] `*.draft.md` 存在
- [ ] **`references_read_in_order` = true**（檔案開頭聲明，證據是寫前讀過 philosophy → content → voice 三份依序）
- [ ] 每條字數 ∈ [80, 300]
- [ ] 整串字數 ≤ 2000
- [ ] **Part C Hard Lint 通過**（結構名沒出現在正文）
- [ ] **User 用編輯眼光審稿過**（寫作品味由 user 判斷，不是機械 lint）
- [ ] **User align**：「草稿讀起來像我嗎」

**REQUIRED NEXT STEP**：進 Stage 6 前，本 Gate 全部 checkbox 必勾。任一未勾 = Gate FAIL = **不得**進 Stage 6。**特別注意**：Part C Hard Lint 是唯一機械擋條件（結構名漏出正文）；寫作品味（贅詞 / 教訓體 / self-deprecation 等）由 user 編輯審把關，AI 不替代。

### Gate 6 → 7

- [ ] `*.review.md` 存在
- [ ] CLI 建議列出
- [ ] User 已決定採納哪幾條
- [ ] 採納的修改已套到 draft
- [ ] **User align**：「這版可以發了嗎」

**REQUIRED NEXT STEP**：進 Stage 7（發文）前，本 Gate 全部 checkbox 必勾。任一未勾 = Gate FAIL = **不得** publish。User 必須在本 session 明說「發」才能跑 `--confirm --yes`。

### Gate 7 — 發文

- [ ] `threads post publish-chain --dry-run` 預覽完成
- [ ] User 看過 dry-run 輸出
- [ ] **User 明確說「發」**才執行 `--confirm --yes`

**REQUIRED NEXT STEP**：發文後寫 published.md，記錄 post_id + published_at + dry_run_confirmed_by_user: true。Pipeline 完成。

---

## Part C：Voice Hard Lint + 寫作技巧筆記

### Hard Lint（唯一一條 Gate FAIL 條件）

寫完每條 post，跑這條 lint：

- [ ] **結構名沒出現在正文**：「認知翻轉鏈」「PREP」「AIDA」「SCQA」「鉤子」「骨架」「Hook」「P1/P2」⋯ 等設計者語言不可在貼文正文出現。讀者語言 ≠ 設計者語言；結構名漏出 = 把 wireframe 當完稿。

**這是唯一的機械 lint 條件**。其他寫作品味問題（用詞節奏 / 自我消毒 / AI 整齊感 / 教訓體）交給 user 在 Stage 5/6 人工審。

### 寫作技巧筆記（why，不是 don't）

下列**不是禁令**，是給 AI 寫稿時的技巧參考。寫完後 user 用編輯眼光審；user 覺得 OK 就 OK，不算 Gate FAIL。

**1. 書面贅詞讓句子變學術**

「其實 / 本質上 / 從某種角度 / 某種程度上」這類詞會讓句子變論文體。例：「**其實**這個方法很簡單」砍掉「其實」更直接。但**有時**「其實」也能傳遞口語感（「其實我也不確定」），看上下文。

**2. 明示列舉讓貼文變課堂**

「首先 / 其次 / 最後」是文章結構詞，Threads 是聊天。例：「先做了 X / 後來做了 Y」比「首先 X，其次 Y」更像跟朋友講話。但**有時**清楚編號也好用（教學類文體）。

**3. 評論體會讓讀者覺得在裝深度**

「值得反思 / 發人深省 / 具有指標意義」是書評語氣。寫了讀者會疏離。換成「我想很久」「我也說不清為什麼」這種更近的句子。

**4. 教訓體違反「分享者不是教學者」哲學**

「所以我們要⋯」「這告訴我們⋯」「結論是⋯」把分享變說教。讀者來看 Threads 是看你的故事，不是聽你下結論。**故事結束就結束**，不必收尾。

**5. Self-deprecation 跟真誠自嘲是兩件事**

- 真誠自嘲（陳述狀態）：「我是個 Threads 新手」「還很粗糙，先放出來」「不熟的就說不熟」 → 讀者讀到覺得真實
- 自我消毒（否定行動價值）：「沒什麼特別的方法」「我也沒做什麼」「就是隨便試試」 → 讀者讀到覺得**疏離**（你都說沒什麼了，那我為什麼要看？）

差別不在禁字，在動機。寫完問自己：這句是「陳述狀態」還是「打折成果」？user 在 review 時會 catch。

**6. AI 整齊感讓人察覺這不是人寫的**

每段字數差不多、句子都完整收尾、沒有口語斷裂 → 讀起來像生成內容。voice-patterns.md「短句頻繁斷行」「煩死了!!!」「斷得比一般人早」就是反向 — 學使用者那種**不整齊**的節奏。

**7. 用對結構名沒問題；用結構名取代寫作不對**

寫骨架時用「PREP / 鉤子」是設計者語言（OK，schema 鼓勵），寫貼文正文時不能讓這些字漏出來（hard lint，見上）。

---

## 與 SKILL.md 的關係

- 本文檔是 SKILL.md 路徑 A 的工程化補充，**不取代** SKILL.md 的流程描述。
- 路徑 A Step 1–5 的順序、CLI 用法、人格與溝通原則 → 看 SKILL.md
- 每個 Step 的產物 schema、Gate 條件、Voice lint → 看本文檔
- 之後 advisor branch merge 進 main 時，SKILL.md 各 Step 結尾應加引用 `→ 進下一步前先查 docs/dev/advisor-pipeline-schema.md Gate N→N+1`

---

## 變更歷史

- 2026-04-27 初版（response to 0424 18:07 三條紀律違規 + pipeline 工程化缺口分析）
