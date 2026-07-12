# Advisor Pipeline Schema 實測報告 — 2026-04-28

> 本份接續 `advisor-pipeline-test-20260427b.md`（Stage 0 端到端）。本次 batch 從 Stage 1 推進到 Stage 5（hold 不發 → 略過 Stage 6 review / Stage 7 publish），完成「pipeline 跑一輪看長什麼樣」的端到端練習。
>
> **測試目標**：用 0428 Stage 0 PASS 的 `drafts/not-good-enough-to-share.angle.md` 當 input，跑一輪完整 Stage 1→6 練習；user 全程編輯眼光把關 + 最後 hold 不發；驗證 schema 在 framework 選擇 / plan 設計 / algo mapping / interaction 設計 / **draft 寫稿（最高 risk）** 場景下擋了什麼、沒擋什麼。
>
> **執行者**：Claude（claude-opus-4-7-1m）扮演 advisor；user 扮演真實寫作者 + 管理者。
>
> **session 結果**：Stage 1–5 全部 Gate PASS；Stage 6+ 由 user hold not publish 略過。

---

## 一、Stage 推進總覽

| Stage | Artifact | Gate 結果 | User align |
|-------|----------|----------|------------|
| 1 framework | `not-good-enough-to-share.framework.md` | PASS | 「Option A — 14 感性觀點 ⋯ 因為比較符合我們的場景與情境」 |
| 2 plan | `not-good-enough-to-share.plan.md` | PASS | 「我覺得可以保留 這也不算表演」（針對 P4 advisor pipeline 例子的 hesitation） |
| 3 algo | `not-good-enough-to-share.algo.md` | PASS | 「好 繼續」 |
| 4 interaction | `not-good-enough-to-share.interaction.md` | PASS | 「好 可以」 |
| 5 draft | `not-good-enough-to-share.draft.md` | PASS（hard lint + char schema + user「寫得不錯」） | 「其實我覺得寫的不錯 但是我不想發」 |
| 6 review | — | 略過 | user hold not publish |
| 7 publish | — | 略過 | user hold not publish |

---

## 二、Schema 擋住的（PASS）

### Stage 1 — framework
- ✅ 強制 3 個 considered（不少不多）
- ✅ 每個 why_fit 非空話
- ✅ chosen_framework.id 必須在 16+1 清單
- ✅ chosen_reason 非禁字（user 給「比較符合我們的場景與情境」， 通過）

### Stage 2 — plan
- ✅ 6 必填章節齊全
- ✅ 骨架每條【鉤子類型】【字數建議】【內容方向】【情緒】
- ✅ 起承轉合 mapping **顯式列表**（非隱在骨架）
- ✅ 總字數 ≤ 3500

### Stage 3 — algo
- ✅ 每條 post 對應 ≥ 1 個機制
- ✅ 機制名稱**全部來自 threads-algorithm-skill 26 機制清單**（grep 從 reference heading 確認 + 含專利編號原文）
- ✅ 每個 mechanism 有 why_applies + risk

### Stage 4 — interaction
- ✅ chosen_types 數量 ∈ {2, 3}（本次選 2）
- ✅ post_position 與 plan.md 骨架對應
- ✅ example_phrasing 非空

### Stage 5 — draft（最嚴格 gate）
- ✅ 每條字數 ∈ [80, 300]（89 / 85 / 87 / 119 / 89）
- ✅ 整串字數 ≤ 2000（469）
- ✅ **Hard Lint「結構名沒漏出正文」PASS**（grep 確認無 PREP / SCQA / 鉤子 / 骨架 / Stage / pipeline 等設計者詞）
- ✅ User 用編輯眼光審稿過（「寫得不錯」）

**結論**：schema 對 Stage 1–5 的「結構性正確」全部擋得住。Hard Lint 擋住結構名漏出正文（Stage 5 最危險的 anti-pattern）。

---

## 三、Schema 沒擋住的 — **新增缺口 4**

### 缺口 4：reference 規定本身有問題（schema 自我矛盾）

**現象**：

Schema Stage 5 規定：

> 進入 Stage 5 前必須在本訊息**依序讀完** `references/writing-philosophy.md` → `references/content-structure.md` → `references/voice-patterns.md` 三份檔，並在 draft.md frontmatter 寫 `references_read_in_order: true`。順序錯 = Gate FAIL。

但實測時：

```bash
$ find . -name "writing-philosophy.md" -o -name "content-structure.md" -o -name "voice-patterns.md"
（無輸出）
```

**這三份檔在 repo 不存在**。schema 0427 設計時放進這條 requirement 但**從沒驗證過 reference 是否存在 / 該包含什麼**。

**user catch**：「這個不是已經有了要用參考的方式來看嗎，怎麼會是補檔哩」

**user reframe**（最 load-bearing）：

> philosophy / content / voice 三類「東西」**已經分散在既有 source**：
> - philosophy → memory `project_content_philosophy.md`（「分享自己而非推銷自己」）
> - content → `references/copywriting-frameworks.md` + plan.md 起承轉合 mapping
> - voice → angle.md frontmatter `source_quotes` + `writing_notes`
>
> Schema 應該規定「**依序 review 三類既有來源**」而不是「依序讀獨立三份檔」。

**為什麼這是個 schema 缺口**：

Schema 自己沒擋「規定 reference 但 reference 不存在」這個情況——schema 在自我 verification 上有盲點。這比缺口 1–3 更深一層：缺口 1–3 是 schema 沒擋某類 anti-pattern；**缺口 4 是 schema 自己的 requirement 本身是 broken 的**。

**修正方向**：

1. 把 schema Stage 5 entry requirement 改成：
   ```
   進入 Stage 5 前必須在本訊息依序 review 三類來源：
   - philosophy: memory project_content_philosophy.md（或 user 特定 angle 的內容哲學 quotes）
   - content: references/copywriting-frameworks.md + 本 case 的 plan.md
   - voice: 本 case 的 angle.md frontmatter（source_quotes + writing_notes）
   ```
   draft.md frontmatter 寫 `references_consulted_in_order: true` 取代 `references_read_in_order: true`。

2. Schema 加 cross-cutting rule：**every requirement must verify its prerequisites exist in current codebase**。寫 schema 時不能只列 aspirational requirement，必須 verify 對應 source 已存在或同步建檔。

---

## 四、更深的 Lesson — Pattern Level

### Lesson：抄 pattern 要逐條驗 fit

0427 14:23 schema 工程化時注入 5 個 superpowers patterns（Iron Law / Stage Entry Template / Plan Failures / REQUIRED NEXT STEP / Voice Hard Lint + 寫作技巧筆記）。當時的設計流程是「**這 5 個 pattern 都很有用 → 全部 inject**」。

但本次 batch surface 出：

- Iron Law / Stage Entry Template / Plan Failures / REQUIRED NEXT STEP — 這 4 個在本次端到端跑都 PASS、確實有用
- **Voice Hard Lint + 寫作技巧筆記** —— 這條的「reference 三份檔依序讀」requirement 是 **untested copy from superpowers source pattern**，沒 verify 我們 codebase 有沒有對應 source

**Lesson**：未來 schema 工程化（or 任何抄 pattern 進 codebase）時，**逐條 question**：

1. 這條 requirement 在**我們 codebase** 真的需要嗎？
2. 對應的 source / artifact / reference **已經存在嗎**？不存在的話要先建還是 reframe？
3. 這條 requirement 跟 user 的實際 workflow 對齊嗎？還是只是 source pattern 的 idiom？

如果哪條過不了 question 2 或 3，就**不該直接抄**，要 reframe 或先建 prerequisite。

---

## 五、Insights —— 端到端跑完後的整體觀察

### 1. Stage 1–4 結構化 stage schema ROI 高

framework / plan / algo / interaction 這 4 個 stage 都是「結構化推導」（從上一 stage artifact + reference 推下一 stage artifact），schema requirement 對應的 evidence 都 grep-able / count-able / range-checkable。Plan Failures + Gate checklist 在這 4 個 stage 把 anti-pattern 擋得乾淨。

### 2. Stage 5 寫稿 stage 的 voice 品味確實靠 user

預期擔心的「voice drift」沒發生—— 但**不是 schema 擋住**，是 user 用「寫得不錯」確認後才算 PASS。Schema 的 hard lint 只擋「結構名漏出」（極具體的設計者詞），其他 voice 品質（教訓體 / 評論體 / self-deprecation 真誠 vs 自我消毒）AI 寫稿時靠**寫作技巧筆記** self-check，最後 user 編輯眼光定奪。

這驗證 0427 設計時的「**程序問題機械擋 / 品味問題 user 編輯眼光把關**」分線。

### 3. 字數壓在下緣

plan 預估 575 chars，實際 469 chars。每條都壓在 schema lower bound 80–90 附近（不是 plan 建議的 100–150）。Threads 短句斷行密度高，**字數短不代表內容稀**。但 schema 應該注意：**plan 預估字數 vs draft 實際字數的 deviation 是合理現象**，不該因此自動視為 violation。

### 4. User 「批次 authorize 連續推進」是高效模式

User 一開頭說「跑一輪完整 Stage 1→6 練習...就看 pipeline 走完長什麼樣」= batch authorization。每個 Gate 之間 user 給簡短 align（「好 繼續」「好 可以」「我覺得可以保留」）+ 最後 Stage 5 編輯審稿——比每個 stage 深度討論更高效，**前提是 angle gate 已 align 銳利**（Stage 0 PASS 真的 align）。

如果 angle gate 沒 align，後面 stage 的 batch authorization 會掩蓋 angle 偏離問題。所以 batch 模式對 angle gate 紀律有更高要求。

---

## 六、下一步建議

### P0：把缺口 4 + Lesson 寫進 schema

- 修改 `docs/dev/advisor-pipeline-schema.md`：
  - Stage 5 entry requirement 從「依序讀三份檔」reframe 為「依序 review 三類既有來源」
  - 把 lesson「抄 pattern 要逐條驗 fit」加進 cross-cutting Iron Law 區塊（可作為 prerequisite verification rule）

### P1：把 0427b + 0428 兩份 pipeline-test 報告的所有缺口（共 4 個）整理為 schema 補強 PR

四個缺口列表：
1. 連續 push（每句合法但累積感）→ turn-level cooldown rule
2. 歧義詞自行 assume → cross-cutting clarify-on-ambiguity rule
3. sharpness 太複雜 → readability lint（→ 符號 / 學術詞 / 字數 / 第一人稱）
4. reference 規定本身 broken → reframe to「依序 review 三類既有來源」+ verify-prerequisite-exists rule

可走 0427 14:23 那種 superpowers writing-plans + executing-plans 流程。

### P2（沿用）

- merge `feat/advisor-plan` 到 main 解 CLI 卡點
- PR #4 / `feat/profile-discovery` / B 路線錄影送審
- 清理 `threads-kanisleo-post.png` / `.playwright-cli/`

---

## 變更歷史

- 2026-04-28 初版（Stage 1→5 端到端練習，hold not publish；surface 缺口 4 + lesson）
