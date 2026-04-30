# Stage 5 — Draft（寫稿，最嚴格 stage）

> **進入 Stage 5 時讀本份 reference IN FULL**——不是掃過、不是摘要。本份是 pipeline 內**唯一**有 binary 機械擋條件（Voice Hard Lint）的 reference。
>
> **同時必讀**：`drafts/<slug>.angle.md` 的 frontmatter `source_quotes`——那是本篇貼文的真實 voice。本 reference 提供的 voice patterns 是 scaffolding，**source_quotes 才是 truth**。

---

## 進入 Stage 5 必做的三件事（缺一 = Gate 5→6 FAIL）

1. **讀本份 reference in full**（包括 Voice Hard Lint 與 7 條寫作技巧筆記）
2. **讀 `drafts/<slug>.angle.md` 的 `source_quotes`**——撈出 user 在 Stage 0 親口說的原話
3. **在 `drafts/<slug>.draft.md` frontmatter 寫 `references_read_in_order: true`**——audit trail，沒這欄位 = 默認沒讀 = FAIL

這三件事的順序：先 1 後 2，最後寫稿時把 `references_read_in_order: true` 帶進 frontmatter。

---

## 為什麼 Stage 5 這麼嚴

0427 schema v1 規定 Stage 5 entry 要讀三份不存在的檔，每次都靠人臨時繞過。本 skill 把那次 incident 內化——loading guarantee 從「依序讀三份檔」改成「**讀本 reference + angle.md source_quotes**」（東西都實際存在），但仍維持「entry 強制讀」的紀律。

寫稿是 pipeline 中 voice drift 風險最高的 stage。Stage 1–4 都是結構化決策（grep-able / count-able），Stage 5 是 voice，最容易 AI 自動腦補。所以 entry 強制讀、`references_read_in_order: true` 強制寫 frontmatter，把品質下限拉住。

---

## Stage 5 Artifact Schema

**檔名**：`drafts/<slug>.draft.md`

**必填欄位**：

```yaml
stage_entry_announced: true
upstream_gate_passed: true
references_read_in_order: true   # 強制 audit trail

posts:
  - position: "P1"
    text: "完整 post 文字"
    char_count: 89
  - position: "P2"
    text: "..."
    char_count: 95
  # ... P3, P4, P5, ...

voice_self_check_results:
  hard_lint_structure_names: pass    # 本份末尾 Voice Hard Lint 唯一硬條件
  voice_aligned_to_source_quotes: pass  # 對齊 angle.md source_quotes
  notes: "AI 自評本次寫稿時哪幾條技巧筆記特別注意，例如：避免教訓體、保留短句斷裂節奏"
```

---

## 字數約束

- 每條 post：**80–300 字元**
- 整串 thread：**≤ 2000 字元**

下限 80 是 Threads 平台節奏需要——太短像沒講完。
上限 300 / 2000 是讀者注意力上限。

字數短不代表內容稀——Threads 短句斷行密度高，89 字配合節奏感可能比 200 字密集排版更紮實。**不要因「字數壓在下限」自動視為 violation**。

---

## Voice Hard Lint（pipeline 內**唯一**的 binary 機械擋條件）

寫完每條 post，跑這條 lint：

- [ ] **結構名沒出現在正文**：「認知翻轉鏈」「PREP」「AIDA」「SCQA」「鉤子」「骨架」「Hook」「P1/P2」⋯ 等**設計者語言**不可在貼文正文出現

讀者語言 ≠ 設計者語言。結構名漏出 = 把 wireframe 當完稿 = Gate FAIL。

**這是唯一的機械 lint 條件**。其他寫作品味問題（用詞節奏 / 自我消毒 / AI 整齊感 / 教訓體）由 user 在 Stage 5/6 用編輯眼光審——AI 不替代 user 的編輯判斷。

---

## 7 條寫作技巧筆記（why，不是 don't）

下列**不是禁令**，是給 AI 寫稿時的技巧參考。寫完後 user 用編輯眼光審；user 覺得 OK 就 OK，不算 Gate FAIL。

### 1. 書面贅詞讓句子變學術

「其實 / 本質上 / 從某種角度 / 某種程度上」這類詞會讓句子變論文體。

例：「**其實**這個方法很簡單」砍掉「其實」更直接。

但**有時**「其實」也能傳遞口語感（「其實我也不確定」），看上下文。

### 2. 明示列舉讓貼文變課堂

「首先 / 其次 / 最後」是文章結構詞。Threads 是聊天，不是論文。

例：「先做了 X / 後來做了 Y」比「首先 X，其次 Y」更像跟朋友講話。

但**有時**清楚編號也好用（教學類文體）——看 angle.md 是哪個方向。

### 3. 評論體會讓讀者覺得在裝深度

「值得反思 / 發人深省 / 具有指標意義」是書評語氣。寫了讀者會疏離。

換成「我想很久」「我也說不清為什麼」這種更近的句子。

### 4. 教訓體違反「分享者不是教學者」哲學

「所以我們要⋯」「這告訴我們⋯」「結論是⋯」把分享變說教。

讀者來看 Threads 是看你的故事，不是聽你下結論。**故事結束就結束**，不必收尾。

### 5. Self-deprecation 跟真誠自嘲是兩件事

- **真誠自嘲（陳述狀態）**：「我是個 Threads 新手」「還很粗糙，先放出來」「不熟的就說不熟」 → 讀者讀到覺得真實
- **自我消毒（否定行動價值）**：「沒什麼特別的方法」「我也沒做什麼」「就是隨便試試」 → 讀者讀到覺得**疏離**（你都說沒什麼了，那我為什麼要看？）

差別不在禁字，在動機。寫完問自己：這句是「陳述狀態」還是「打折成果」？user 在 review 時會 catch。

### 6. AI 整齊感讓人察覺這不是人寫的

每段字數差不多、句子都完整收尾、沒有口語斷裂 → 讀起來像生成內容。

學使用者那種**不整齊**的節奏：
- 短句頻繁斷行
- 「煩死了!!!」型 punctuation
- 斷得比一般人早（半句就斷）

**source_quotes 是 voice 真理**。AI 自己想出的整齊節奏 ≠ user 的真實節奏。

### 7. 用對結構名沒問題；用結構名取代寫作不對

寫骨架（Stage 2）用「PREP / 鉤子」是設計者語言（OK，schema 鼓勵）。
寫貼文正文（Stage 5）不能讓這些字漏出來（Hard Lint，見上）。

---

## Voice Self-Check（寫完每條 post 跑）

Hard Lint 之外，寫完後 AI 應 self-check 下列再交 user 審：

- [ ] 是否避免上述 7 條技巧筆記提到的 anti-patterns？
- [ ] 句子節奏是否對齊 angle.md `source_quotes` 的真實 voice（不是 AI 自己腦補的整齊節奏）？
- [ ] 是否有教訓體 / 評論體 / 制式 CTA 的傾向？
- [ ] 字數每條都在 80–300 範圍？整串 ≤ 2000？

self-check 結果記到 `voice_self_check_results.notes` 欄位。**self-check pass 不代表 Gate PASS**——還要過 user 編輯眼光那關。

---

## Plan Failures（含以下任一即 Gate 5→6 FAIL）

- `references_read_in_order` 欄位缺 或 false
- 任一 post `text` 為空 或 含「（待寫）」
- 任一 post 字數 ∉ [80, 300]
- 整串字數 > 2000
- **含結構名**（「PREP」「鉤子」「骨架」「P1/P2」⋯）出現在正文 — 唯一 hard lint
- `voice_self_check_results` 未填寫
- **寫作品味問題**（贅詞 / 評論體 / 教訓體 / self-deprecation / AI 整齊感）→ **不是 Plan Failure**，由 user 在 Stage 5/6 用編輯眼光審

---

## Gate 5 → 6 Checklist（pipeline 內最嚴的 gate）

進 Stage 6 前，本訊息逐條跑：

- [ ] `drafts/<slug>.draft.md` 存在
- [ ] **`references_read_in_order` = true**（檔案 frontmatter 聲明，證據是寫前讀過本 reference + angle.md source_quotes）
- [ ] 每條字數 ∈ [80, 300]
- [ ] 整串字數 ≤ 2000
- [ ] **Voice Hard Lint 通過**（結構名沒出現在正文）
- [ ] `voice_self_check_results` 已填寫
- [ ] **User 用編輯眼光審稿過**（寫作品味由 user 判斷，不是機械 lint）
- [ ] **User align**：「草稿讀起來像我嗎」明確發生於本 session

任一未勾 = Gate FAIL = **不得**進 Stage 6。

**特別注意**：Voice Hard Lint 是唯一機械擋條件（結構名漏出正文）；寫作品味（贅詞 / 教訓體 / self-deprecation 等）由 user 編輯審把關，AI 不替代。
