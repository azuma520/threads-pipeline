# Advisor Pipeline Schema 實測報告 — 2026-04-27 (b)

> 本份是 0427 第二次測試（前一份 `advisor-pipeline-test-20260427.md` 是 fixture replay，本份是 fresh session、真實使用者、多回合對話的 Stage 0 端到端測試）。
>
> **測試目標**：驗證 `docs/dev/advisor-pipeline-schema.md`（5 個 superpowers 紀律模式注入版）在「fresh session + 真實對話 + Stage 5 寫稿」場景下擋不擋得住。本次只跑到 Stage 0（Stage 1 被 user 主動 hold，理由見下）。
>
> **執行者**：Claude（claude-opus-4-7-1m）扮演 advisor（Stage 0 angle gate 訪談者）；user 扮演真實 Threads 發文者。
>
> **session 結果**：Stage 0 PASS，產出 `drafts/not-good-enough-to-share.angle.md`；Stage 1 由 user 主動 defer（「保持標準 + 建解法」這個 angle 在工具驗證完成前不發）。

---

## 一、Schema 擋住的（PASS）

| Schema 條件 | 是否擋住 | 證據 |
|------------|---------|------|
| Stage 0 entry announcement | ✅ | AI 第一個訊息使用 Stage Entry Template，列出 upstream / produces / schema requirements |
| `angle.md` 5 個必填欄位齊全 | ✅ | topic / sharpness / reader_value / source / source_quotes 都有實值 |
| `source` ∈ {co_created, observed, quoted} | ✅ | 寫成 `co_created` 並有理由 |
| `source_quotes` 非空且為 user 原話 | ✅ | 6 條 user 原話直接 paste（非改寫） |
| Source label 強制（AI 帶觀察進場） | ✅ | Turn 1 / Turn 5 / Turn 6 三次帶觀察進場全部用明示 phrase（「這是我個人的觀察」/「我從你話裡聽到的」） |
| 落檔前 user align | ✅ | Turn 13 user 「對 是這樣」明確點頭才寫檔 |
| `stage_entry_announced: true` 寫入 frontmatter | ✅ | 寫入 |
| Plan Failures（topic 含 TBD / sharpness 是 surface description / reader_value 寫「分享經驗」空話 / 含佔位文字） | ✅ | 全部規避 |

**結論**：Schema 對 Stage 0 artifact 的「**結構性正確**」擋得住。

---

## 二、Schema 沒擋住的（IMPROVEMENT NEEDED）

這次 session 出現 3 個 anti-pattern，schema 都沒擋。每個都是 user 主動 catch 才修正的。

### 缺口 1：AI 連續兩 turn 軟性 push 同方向

**現象**：

- Turn 5：AI 帶觀察「高標準把你卡住」進場 → user pushback「難道不是嗎」
- Turn 6：AI 立刻又帶另一個觀察「保持標準 + 建解法」進場（包成問句）→ user 部分接受但同時 catch「悖論」
- Turn 7：AI 還在這個 framing 繼續推（誤讀為「被推著下結論」+ 自我譴責推太用力）

**為什麼 schema 沒擋**：

Schema 的 source label 規則只擋 *單句* 是不是有 source phrase（「這是我個人的觀察」）。它沒擋 *連續多 turn 都是「AI 主導的軟性框架推進」* 這種累積感。

每一句單獨看都「合法」（標 source、用問句、留 escape hatch），但連起來 user 感受到的是「AI 一直在推一個方向」。這是個 *cumulative-only* 的 anti-pattern，single-message lint 抓不到。

**user 給的 catch phrase**：「**有點悖論的感覺了**」（雖然 AI 誤讀，但 user 的真實感受夾雜了「對話走得太累」）

**建議補強**：

在 Schema Stage 0 加一條 turn-level 規則：

> **Cooldown rule**：連續 2 turn 都帶觀察進場（即使有 source label）後，下一 turn 必須是純發問形式（不帶觀察），把 frame 還給 user。

或在 angle-gate skill 加：

> 帶觀察進場 ≥ 2 次後，用「user 還在 surface 嗎，還是我已經在主導？」自檢。如果是後者，下 turn 退回純問答。

### 缺口 2：AI 對歧義詞自行 assume，沒 ask clarify

**現象**：

- Turn 6：user 說「**有點悖論的感覺了**」（中文同音「悖論 / 被論」）
- Turn 7：AI 把「悖論」聽成「被論」（被推著下結論）→ 退錯方向 → user 不得不在 Turn 9 再次重述「**有點悖論的感覺**」AI 才意識到誤讀

**為什麼 schema 沒擋**：

Schema 沒對「AI 自行 assume 模糊詞語意」做任何擋。Iron Law 雖然強調「不靠 stale memory」，但對 *當下這條訊息* 的歧義語意，沒要求 ask clarify。

**這個 anti-pattern 在 Stage 5 寫稿場景會更危險**：user 給 voice direction（「不要太剛硬」/「再個人一點」）這種詞語意更模糊，AI 自行 assume 後寫出來的稿可能完全偏掉。

**建議補強**：

在 Schema 加一條跨 Stage 的 cross-cutting rule：

> **Clarify-on-ambiguity rule**：聽到關鍵詞（對 angle / topic / voice 有 framing 影響）且 AI 內心有 ≥ 2 個合理 interpretation 時，必須 ask user 點明，不准自行 assume。**Test**：如果你內心 fork 出「她可能是 X 也可能是 Y」，phrase 改成 question 給 user 選。

### 缺口 3：Sharpness 寫太複雜，schema 沒對「白話度 / 共鳴度」做擋

**現象**：

- Turn 11：AI propose 落檔前 yaml：

  ```yaml
  sharpness: 我想分享『保持標準 + 建解法』，但工具都還沒證實真的有用
    → 不能發 → 驗證可能很久 → 可能永遠卡在『想發但又不能發』之間
  ```

- user catch：「**我反而覺得我們說的事情太複雜了 所以你要做的事情應該是要把我複雜的想法用更通俗易懂的方式表達，這樣我們的受眾也比較看得懂對吧 我們的目標步是要讓售種共鳴嗎 所以這一步應該是最基本的**」

**為什麼 schema 沒擋**：

Schema Plan Failures 對 sharpness 的擋只擋 surface description（重述題目而非銳利切入）。但 sharpness 太複雜、太邏輯化、用 → → → 因果鏈來描述，schema 不視為 violation——技術上它是「銳利切入」，但讀者根本看不下去。

**這個 anti-pattern 直接違反 Threads 平台特性**：Threads 是聊天平台，不是論文平台。Sharpness 寫成「論述體」會讓後續 Stage 5 的 draft 也變論述體。

**建議補強**：

在 Schema Stage 0 Plan Failures 加：

- `sharpness` 含 `→` 邏輯符號（因果鏈式論述體）
- `sharpness` 含「悖論 / 矛盾 / 二元 / 結構」這類抽象學術詞
- `sharpness` 單句 > 60 字（過長代表沒收斂）
- `sharpness` 第一人稱開頭（「我...」）vs 描述體開頭——前者更貼近 Threads 聊天氣質，建議默認用第一人稱

或在 落檔前加一條 lint：

> **Sharpness readability check**：把 sharpness 唸出聲。如果聽起來像 paper abstract / 商業簡報 / 邏輯推導，重寫成「跟朋友聊天會怎麼講」。

---

## 三、Insights —— Schema 是 floor 不是 ceiling

本 session 最重要的觀察：

**Schema 的角色是「擋低分」**（防止 0424 18:07 那種「跳步驟、self-deprecation 漏出、reference 反序讀」的純 procedural violation）。

**它不是「保證高分」**——angle.md 的 sharpness 寫得通俗、有共鳴、有共創氣質，這個品質完全來自 user 在對話中的 catch（「太複雜了」「不知道大家跟我有沒有一樣的處境」），不是 schema fire 出來的。

這證實了 0427 早上 plan 設計時 user 那條最 load-bearing 的 reframing：「**程序問題機械擋、品味問題 user 編輯眼光把關**」。

**但本 session 也 surface 出一個之前沒想到的中間層**——「程序問題 + 品味問題之間的灰色地帶」：

- 連續 push（缺口 1）：表面是程序（每句合法），實質是品味（讓 user 覺得被推）
- 歧義詞 assume（缺口 2）：表面是溝通（語意理解），實質是程序（可以加 clarify rule 機械擋）
- Sharpness 太複雜（缺口 3）：表面是品味（語感判斷），實質可以加部分機械擋（→ 符號 / 學術詞 / 字數 / 第一人稱）

**這三個缺口的補強建議都是「軟性程序 lint」**——不像「每條 post 字數 ∈ [80, 300]」那樣 binary，但比「教訓體」那種完全靠人判斷又進一步——是可以 grep specific signal 的 *中間層* lint。

---

## 四、下一步建議

### P0：把本份報告的三個缺口補進 schema

具體 PR 建議：

1. **Schema cross-cutting 加「Clarify-on-ambiguity rule」**：放在 Iron Law 區塊下面，跨 Stage 適用
2. **Schema Stage 0 Plan Failures 加 sharpness readability lint**：→ 符號 / 學術詞 / 字數 / 句法
3. **Schema Stage 0 加 turn-level cooldown rule**：連續 2 turn 帶觀察後下 turn 純發問

### P1：跑 Stage 5 寫稿場景測試

本份只測到 Stage 0。Stage 5（寫稿）才是 schema 設計時最擔心的「voice drift」場景。需要跑一次完整 Stage 1→6，特別測：

- 連續 push 在寫稿階段會不會把 voice 推向 AI 整齊感
- 歧義詞 assume 在 voice direction 上更危險（user 說「再個人一點」AI 可能 assume 成「加 emoji」）
- Plan Failures 的「結構名漏出正文」在多回合修稿中的擋法

但 P1 要等 user 願意跑一個「現在就能發」的題目，本次 session 的 angle 已被 user defer。

### P2：跟 angle-gate skill 對齊

本次 session 的 anti-pattern 一部分（缺口 1：連續 push）angle-gate skill 已經有警示（「使用者反駁你的觀察後你還堅持」+「使用者繞圈時你拉他回重點」這類 rationalization）。但 *連續多 turn 累積* 這個現象 skill 沒明說。

建議在 angle-gate skill 的 Red flags 加一條：

> 連續 2 turn 都「帶觀察 + 包問句」即使每句合法 → 視為紅旗。下 turn 退回純發問。

---

## 五、本 session 的 deliverable 清單

- ✅ `drafts/not-good-enough-to-share.angle.md`（Stage 0 artifact，Gate 0→1 PASS）
- ✅ `docs/dev/advisor-pipeline-test-20260427b.md`（本份，Schema 實測報告）
- 🟡 Stage 1+ defer（user 主動 hold「保持標準 + 建解法」angle 直到 advisor pipeline 工具驗證完成）

---

## 變更歷史

- 2026-04-27（b）初版（fresh session 真實對話 Stage 0 端到端測試）
