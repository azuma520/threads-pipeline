---
name: threads-write-post
description: "Use when the user wants to write a Threads post end-to-end after the angle is locked — pick framework, plan thread skeleton, map algorithm mechanisms, design interaction, draft, review, publish. Triggers: user says 「幫我寫貼文」/「從 angle 寫到發文」/「跑 advisor pipeline」/「我有 angle.md 了下一步是」, asks to continue from an existing drafts/*.angle.md, or wants the full Stage 1→7 workflow. PREREQUISITE: angle.md must exist (run `threads-angle-gate` first if it doesn't). Do NOT use for Stage 0 angle decisions — that is `threads-angle-gate`'s job. Do NOT use for pure CLI ops (publish/list/insights) — that is `threads-cli`. Do NOT use for analytics-only queries — that is `threads-advisor analyze`."
---

# threads-write-post — Threads 貼文寫作 pipeline（Stage 1→7）

## 這個 skill 是什麼

從一份已銳利的 `angle.md` 出發，把貼文寫到能發出去。Stage 0（想清楚切入點）由 `threads-angle-gate` 處理；本 skill 接 Stage 1–7：選框架 → 規畫骨架 → 演算法機制對應 → 互動設計 → 寫稿 → 讀稿 → 發文。

**檔名規範**：每個 stage 的 artifact 寫在 `drafts/<slug>.<stage>.md`。`<slug>` 跨 stage 一致，由 Stage 0 的 `angle.md` 決定。

**為什麼需要這個 skill**：寫貼文流程曾經完全依賴 `docs/dev/advisor-pipeline-schema.md` 這份契約文件。0428 端到端測試發現 schema 在 Stage 5 入口邏輯卡死——它規定要讀三份不存在的檔，每次都靠人臨時繞過。本 skill 把那份 schema 的規範重組成「skill 內建 reference + 律定何時讀」的結構，schema 文件 deprecate 成歷史紀錄。

**前置條件（必）**：`drafts/<slug>.angle.md` 存在且 Gate 0→1 PASS。沒有 angle.md 不要進 Stage 1，回去跑 `threads-angle-gate`。

---

## Pipeline Iron Law（凌駕全文件，跨 stage 適用）

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
| Stage 5 reference 讀過 | `references_read_in_order: true` 寫進 frontmatter + `stage-5-draft.md` 與 angle.md `source_quotes` 都讀於本 session | 「我有印象讀過」 |
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

## Stage Entry Template（每進一 stage 必跑）

每進入一個 Stage，**第一個訊息必須以下列格式 announce**（不可省略；省略 = 跳 Stage = Iron Law violation）：

```
I'm entering Stage N — <stage name>.
- Upstream artifact: <path to upstream artifact>
- Upstream Gate status: <PASS / FAIL — 評估結果摘要>
- This stage produces: <path to this stage's artifact>
- Schema requirements: <列出本 stage 所有必填欄位>
- Required references to read (if any): <列出檔名 + 順序>
```

並在本 stage 產出的 artifact frontmatter 加：

```yaml
stage_entry_announced: true
upstream_gate_passed: true
references_read_in_order: true   # Stage 5 only — 見 Stage 5 嚴格條件
```

未做 announce 視為「跳 Stage」。`stage_entry_announced` 欄位是強制 audit trail，不可省略。

---

## Stage 0 — Angle（delegated）

**本 skill 不處理 Stage 0**。執行 `threads-angle-gate` skill，產出 `drafts/<slug>.angle.md`，Gate 0→1 PASS 後再回來。

Gate 0→1 沒 PASS（angle.md 缺 sharpness / source_quotes 空 / user 沒明確 align）= 不准進 Stage 1。

---

## Stage 1 — Framework pick

**Artifact**：`drafts/<slug>.framework.md`

**進入時必讀**：When entering Stage 1, read `references/stage-1-framework.md` in full BEFORE producing the artifact. Do not summarize from memory — 16+1 框架名稱與公式必須引用 reference 原文。

**簡要 schema**（complete spec 在 reference）：
- `considered_frameworks`：3 個框架（不少不多），每個含 `id` / `name` / `formula` / `why_fit`
- `chosen_framework`：使用者選定（單一），含 `id` / `name` / `chosen_reason`

**Gate 1→2 提醒**：考慮數 ≠ 3、`chosen_framework.id` 不在 16+1 清單、`chosen_reason` 為空（「順手選」也算空）= Gate FAIL。完整 checklist 見 reference 末尾。

---

## Stage 2 — Plan

**Artifact**：`drafts/<slug>.plan.md`

**進入時必讀**：When entering Stage 2, read `references/stage-2-plan.md` in full BEFORE producing the artifact. Do not summarize from memory — 6 章節結構與字數預算必須對齊 reference。

**簡要 schema**（complete spec 在 reference）：
- 6 個必填章節（依序）：頭部 / 受眾 / 起承轉合 mapping / 骨架 / 互動設計 / 風險提示
- 骨架每條含【鉤子類型】【字數建議】【內容方向】【情緒】
- 總長 ≤ 3500 字

**Gate 2→3 提醒**：缺章節、骨架欄位漏、起承轉合 mapping 隱在骨架內未顯式列出、字數超過 = Gate FAIL。

**對應 CLI**：`advisor plan --framework N --overwrite`（feat/advisor-plan branch 未 merge）。CLI 不可用時 mimic，但必須符合 reference schema。

---

## Stage 3 — Algo mapping

**Artifact**：`drafts/<slug>.algo.md`

**進入時必讀**：When entering Stage 3, read `references/stage-3-algo.md` in full BEFORE producing the artifact. Do not summarize from memory。

**另需 consult**：global `threads-algorithm-skill` 的 26 機制清單。**不准編造機制名稱**——機制名必須引用 `threads-algorithm-skill` 原文。

**簡要 schema**（complete spec 在 reference）：
- 每條 post 對應 ≥ 1 個機制：`post_position` / `mechanism` / `why_applies` / `risk`
- 整體：`dominant_mechanisms`（2–3 個）/ `avoid_mechanisms`（如 Low Signal）

**Gate 3→4 提醒**：機制名未引用 `threads-algorithm-skill` 原文、`why_applies` / `risk` 為空 = Gate FAIL。

---

## Stage 4 — Interaction design

**Artifact**：`drafts/<slug>.interaction.md`

**進入時必讀**：When entering Stage 4, read `references/stage-4-interaction.md` in full BEFORE producing the artifact. Do not summarize from memory。

**簡要 schema**（complete spec 在 reference）：
- `chosen_types`：5 類型中選 2–3 個（不接受 1 個或 4+）
- 5 類型：開放式問題 / 爭議觀點 / 個人經驗邀請 / 投票選擇題 / 標記朋友
- 每個 chosen type 含 `post_position` / `why_this_post` / `example_phrasing`

**Gate 4→5 提醒**：`chosen_types` 數量 ∉ {2, 3}、`example_phrasing` 為空（Stage 5 將無從寫起）、自創類型 = Gate FAIL。

---

## Stage 5 — Draft（CRITICAL — 嚴格 loading guarantee）

**Artifact**：`drafts/<slug>.draft.md`

### 進入時必做三件事（缺一 = Gate 5→6 FAIL）

**(a) 讀 `references/stage-5-draft.md` in full**——voice patterns、Voice Hard Lint、7 條寫作技巧筆記都在這份檔。Voice Hard Lint 是 pipeline 內**唯一**的 binary 機械擋條件，跳過會讓結構名漏出正文。

**(b) 讀 `drafts/<slug>.angle.md` frontmatter 的 `source_quotes`**——這是 user 本篇貼文的真實聲音。stage-5-draft.md 提供的 voice patterns 是 scaffolding（短句斷行 / 不整齊節奏 / 「煩死了!!!」型 punctuation），但**特定本篇的 voice 真理在 source_quotes**。AI 自己腦補的 voice ≠ user 的 voice。

**(c) 在 draft.md frontmatter 寫 `references_read_in_order: true`**——這是 audit trail 證據。沒這欄位 = 默認沒讀 = Gate FAIL。

### 為什麼 Stage 5 特別嚴

0427 schema v1 在 Stage 5 入口要求「依序讀三份檔」（philosophy / content / voice），但那三份檔當時不存在。0428 跑 fresh session 時 AI 直接違規寫稿、frontmatter 硬填讀過了。這個 skill 設計時把那次 incident 內化為**強化版 loading guarantee**——三件事缺一即 FAIL，不是 nice-to-have。

### 簡要 schema（complete spec 在 reference）

- `posts`：N 條完整文字，每條 `position` / `text` / `char_count`
- `references_read_in_order`：true（audit trail）
- `voice_self_check_results`：reference 內的 self-check checklist 通過記錄
- 字數：每條 80–300 / 整串 ≤ 2000

### Gate 5→6 提醒

`references_read_in_order` 缺、字數超範圍、整串字數 > 2000、結構名（PREP / 鉤子 / SCQA / Hook / P1/P2 ⋯）漏出正文 = Gate FAIL。寫作品味問題（贅詞 / 評論體 / 教訓體 / self-deprecation / AI 整齊感）**不是 Gate FAIL**，由 user 在 Stage 5/6 用編輯眼光審。

---

## Stage 6 — Review（CLI inline）

**Artifact**：`drafts/<slug>.review.md`

### 步驟

1. 跑 CLI：`threads-advisor review drafts/<slug>.draft.md`
2. CLI 吐出 6 維度建議（鉤子 / 焦點 / 收穫 / position 一致性 / 受眾匹配 / 結構）
3. 把 CLI 原始建議完整貼進 `review.md` 的 `cli_suggestions` 欄位
4. 跟 user 一起決定採納哪幾條，寫進 `user_accepted` 欄位
5. 採納的修改套回 `draft.md`，`applied_to_draft: true`

### Gate 6→7 提醒

- `cli_suggestions` 為空（CLI 沒跑或 output 沒貼）
- `user_accepted` 未明確列出哪幾條
- `applied_to_draft: true` 但 draft.md 未實際更新
- 跳過 `advisor review` CLI 直接宣告 review 完成

任一 = Gate FAIL。

---

## Stage 7 — Publish（CLI inline）

**Artifact**：`drafts/<slug>.published.md`

### 步驟

1. dry-run 預覽：`threads post publish-chain drafts/<slug>.draft.md --dry-run`
2. user 看 dry-run 輸出，**user 必須在本 session 明確說「發」**才能進下一步
3. 真發：`threads post publish-chain drafts/<slug>.draft.md --confirm --yes`
4. 寫 `published.md`：`post_id` / `published_at` / `dry_run_confirmed_by_user: true`

### Gate 7（發文前最後一道）

- `--dry-run` 預覽完成
- user 看過 dry-run 輸出
- **user 明確說「發」**才執行 `--confirm --yes`
- 發文後 `post_id` 寫進 published.md

未跑 dry-run 直接 `--confirm --yes` / `dry_run_confirmed_by_user: false` 卻 publish / `post_id` 為空 = 違規。

---

## 什麼時候不要用這個 skill

- **Stage 0 angle 還沒鎖定** → 用 `threads-angle-gate`。本 skill 拒絕在沒有 Gate 0→1 PASS 的 angle.md 上開工。
- **要修現有 draft、不重寫** → 直接 `threads-advisor review drafts/<slug>.draft.md`，不必跑全 pipeline。
- **純 CLI ops**（發、查、刪、insights） → 用 `threads-cli`。
- **要看歷史數據做決策** → 用 `threads-advisor analyze`。
- **要重想角度（推翻現有 angle.md）** → 退回 `threads-angle-gate` 重跑 Stage 0，不要在本 skill 內 patch。

---

## Reference files

本 skill 採 conditional loading——進入 Stage N 時讀對應 reference，不要一次全載：

| Reference | 何時讀 | 涵蓋 |
|---|---|---|
| `references/stage-1-framework.md` | 進入 Stage 1（選框架）時 | 16+1 框架公式 + 4 類結尾 + 選擇指南 + Gate 1→2 checklist |
| `references/stage-2-plan.md` | 進入 Stage 2（規畫骨架）時 | 6 章節結構 + 字數預算 + 骨架欄位規範 + Gate 2→3 checklist |
| `references/stage-3-algo.md` | 進入 Stage 3（演算法 mapping）時 | mapping 規則 + 主訴/避開機制 + 指向 `threads-algorithm-skill` + Gate 3→4 checklist |
| `references/stage-4-interaction.md` | 進入 Stage 4（互動設計）時 | 5 類型 + 數量規則（2–3） + example_phrasing 規範 + Gate 4→5 checklist |
| `references/stage-5-draft.md` | 進入 Stage 5（寫稿）時 — **強制讀 in full** | voice patterns + Voice Hard Lint + 7 條寫作技巧筆記 + voice_self_check checklist + Gate 5→6 checklist |

Stage 6 / Stage 7 步驟 inline 在本 SKILL.md 裡（CLI 命令很短，抽 reference 反而空殼）。

---

## 跟其他 skill 的關係

- **`threads-angle-gate`**（Stage 0）：本 skill 的前置。沒有它的 angle.md 不准開工。
- **`threads-algorithm-skill`**（global）：Stage 3 必 consult，提供 26 機制清單。**不要編造機制名稱**。
- **`threads-cli`**：Stage 7 publish 透過它的 `threads post publish-chain` 命令；Stage 6 review 透過 `threads-advisor review`（advisor 在 `threads-cli` 旁的姊妹 binary）。
- **`threads-advisor analyze`**：跟本 skill 平行——分析既有發文表現、不寫新貼文。

## 變更歷史

- 2026-04-30 v1：取代 `docs/dev/advisor-pipeline-schema.md` 作為 Stage 1–7 的 source of truth。把 schema 規範重組成 skill body + 5 份 reference + conditional loading。Stage 5 reference 從「依序讀三份不存在的檔」改成「讀 stage-5-draft.md + angle.md source_quotes」（修補 schema 0427 v1 的 reference broken 缺口）。
