# Stage 2 — Plan（thread 骨架規畫）

> **進入 Stage 2 時讀本份 reference in full**。6 章節結構與字數預算必須對齊本份規範。

---

## 這個 stage 在做什麼

Stage 2 把 angle.md 的銳利點 + framework.md 的選定框架，展開成可寫稿的 **thread 骨架**——多少條 post、每條的鉤子類型、字數建議、內容方向、情緒。

**不是寫稿**。骨架描述「這條 post 講什麼方向」，不是把成稿寫出來。

---

## Stage 2 Artifact Schema

**檔名**：`drafts/<slug>.plan.md`

**必填 frontmatter 欄位**（每 stage artifact 共通）：

```yaml
stage_entry_announced: true
upstream_gate_passed: true
```

**必填章節（依序，缺一即 Gate FAIL）**：

### 1. 頭部
- 題目（從 angle.md `topic` 來）
- 框架編號 + 名稱（從 framework.md `chosen_framework` 來）
- 格式（thread / single）
- 預估總字數

### 2. 目標受眾
- 誰會想讀（1–2 句具體描述，不是「對 X 有興趣的人」這種空話）
- 痛點動機（為什麼這群人會停下來讀）

### 3. 起承轉合 mapping
- **顯式列出**：哪段對應「起」、哪段對應「承」、哪段對應「轉」、哪段對應「合」
- 不可隱在骨架裡——必須單獨一節點明
- 用 framework 公式對應（例：PREP 的 Point → 起 / Reason → 承 / Example → 轉 / Point → 合）

### 4. 骨架（thread 主體）

每條 post 必須含四個欄位：

```
## P1
- 【鉤子類型】反問 / 對比 / 數字 / 衝突 / 故事⋯
- 【字數建議】80–120 字
- 【內容方向】2–3 句指引（**不是成稿**），例：「丟出反直覺問題：為什麼 X 越用越累？回 1 句帶出本篇主軸」
- 【情緒】不安 / 好奇 / 共鳴 / 釋然⋯
```

「內容方向」是**指引**不是成稿。寫成稿是 Stage 5 的事；Stage 2 寫太細會把 Stage 5 的彈性卡死。

### 5. 互動設計
- 結尾 CTA 類型（互動式 / 夥伴式 / Slogan / 反轉式——見 stage-1-framework.md 的 4 類結尾）
- 可加的互動元素提示（哪幾條 post 適合放互動，具體哪類在 Stage 4 細化）

### 6. 風險提示
- LLM 自評骨架可能弱點 1–2 點
- 例：「P3 的轉折太突兀，讀者可能跟不上」「整串偏教訓體，需 Stage 5 寫稿時 catch」

---

## 字數約束

- 整份 plan.md 總長 **≤ 3500 字元**（含所有章節）
- 預估總字數（頭部欄位）依 thread 設計，不必在這階段精算

---

## 對應 CLI

`advisor plan --framework <N> --overwrite`（feat/advisor-plan branch 未 merge）

CLI 不可用時 mimic，但必須符合本 reference 的 schema。Mimic 不是免責標籤——所有欄位仍要齊。

---

## Plan Failures（含以下任一即 Gate 2→3 FAIL）

- 缺任一必填章節（頭部 / 受眾 / 起承轉合 mapping / 骨架 / 互動設計 / 風險提示）
- 骨架某條缺【鉤子類型】或【字數建議】或【內容方向】或【情緒】
- 內容方向寫成「成稿」（schema 規定 2–3 句指引）
- 含「（空白）」「（之後填）」「TBD」「待寫」
- 起承轉合 mapping 隱在骨架內未顯式列出
- 總字數 > 3500
- 沒寫風險提示（每篇都有 trade-off，必須列）

---

## Gate 2 → 3 Checklist

進 Stage 3 前，本訊息逐條跑：

- [ ] `drafts/<slug>.plan.md` 存在
- [ ] 6 個必填章節都在（頭部 / 受眾 / 起承轉合 mapping / 骨架 / 互動 / 風險）
- [ ] 骨架每條都含【鉤子類型】【字數建議】【內容方向】【情緒】
- [ ] **起承轉合 mapping 顯式列出**（不是隱在骨架裡）
- [ ] 總字數 ≤ 3500
- [ ] **User align**：「骨架結構對嗎，有沒有要重做」明確發生於本 session

任一未勾 = Gate FAIL = **不得**進 Stage 3。
