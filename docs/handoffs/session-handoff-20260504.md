# Session Handoff — 2026-05-04

## Session 08:06

### 一、今日聚焦

開工讀接力棒，等待 user 決定本 session 走 P0（用其他主題再跑 threads-write-post skill 驗證）還是先處理其他臨時任務。

### 二、完成事項

- 讀 `docs/handoffs/session-handoff-20260430.md` Session 17:24 收工回寫 + `memory/project_progress_20260430.md`
- 摘要 0430 接力棒給 user：P0 用其他主題跑 skill / P1 Stage 6/7 + advisor-plan 收尾 / P2 清檔；附帶提醒 0430 17:24 區塊（117 行）還在 dirty 狀態未 commit
- 等 user 指示

### 三、洞見紀錄

無（session 剛開工尚未動手）

### 四、阻塞 / 卡點

無

### 五、行動複盤

無

### 六、檔案異動

- 新增：`docs/handoffs/session-handoff-20260504.md`（本檔，session 雛形）

### 七、收工回寫

- [ ] **Memory**：本 session 若有實作再決定是否新增 `project_progress_20260504.md`
- [ ] **MEMORY.md 索引**：同上
- [ ] **下次 session next action**：沿用 0430 17:24 接力棒（P0 / P1 / P2 不變），除非本 session 有實作改變狀態

---

## Session 14:14

### 一、今日聚焦

threads-write-post v2 升級全程：brainstorm 寫作哲學 → spec → plan → 8 task subagent-driven 落地。從 user 抱怨「AI 共寫產出不穩 / 變教人 / 過度修剪四不像」這個痛點 surface，一路把 design 跑到 8 commits 落地 main。

### 二、完成事項

- **brainstorming session 跑完整流程**：8 個 checklist 全跑（context exploration / clarifying / 3 approaches / design sections / spec doc / self-review / user review / writing-plans 銜接）
- **寫作哲學主軸 settle**：「**show, don't tell**——觀點及思考都是過程的判斷而來，要透過過程及結果表達出觀點與思考，不要告訴讀者主角是怎樣的人，用他的選擇與做法呈現。」（user 自己 phrase 出的版本，比我跟 Codex 的草稿都精準）
- **Codex 第二觀點 dial-in**：把對話脈絡丟 Codex 獨立歸納，補強 5 個我漏的 catch（被迫進入教師姿態 / 動機防衛性 / utility+affinity 不是 trade-off / 可檢驗第一人稱判斷 / thesis+detail mutually constitutive）
- **spec doc 落地**：`docs/superpowers/specs/2026-05-04-threads-write-post-v2-design.md`（gitignored，~280 行，5 sections + 風險 + 驗證 + 後續步驟）
- **plan doc 落地**：`docs/superpowers/plans/2026-05-04-threads-write-post-v2.md`（gitignored，9 tasks，每個含完整 file path + content + verify + commit）
- **subagent-driven-development workflow 跑通**：T1-T8 各派 implementer (Haiku) + spec reviewer (Haiku) + code quality reviewer (Haiku，superpowers:code-reviewer agent type)，T8 完成後 final reviewer (Sonnet) 跑全 diff cumulative review。0 task BLOCKED / NEEDS_CONTEXT。
- **8 commits 落 main**：e005df7 (T1 writing-philosophy.md) / de51a57 (T2 stage-1 加 2 frameworks) / fb35274 (T3 stage-5 字句 lint) / 2c2dd5e (T4 SKILL.md Stage 1 entry) / 17e70d3 (T5 Stage 5 entry + lint_passed) / 8d5b71d (T6 Reference table) / 6121e7e (T7 變更歷史 v2) / a04739b (T8 CLAUDE.md skill bullet)
- **0430 dirty handoff 收乾淨**：開工前先 commit 0430 17:24 區塊 117 行（458b0b8）

### 三、洞見紀錄

#### 1. User 自己 phrase 出的哲學主軸 > AI 草擬版本（一條軸 vs 5 段 dimensions）

我先寫 5 段哲學草稿（為什麼寫 / 什麼有價值 / 讀者拿走什麼 / 寫的時候 / 形式），Codex 評「整理得太正確、像穩健清單」+ 「user 真正要的是重心轉移，從『我要給讀者什麼』轉成『我要把哪種思考暴露出來』」。User 直接 phrase 出 **「show, don't tell」一條軸**——把我 5 段 dimensions 全收進去。

**How to apply**：哲學 / first-principle 文件，AI 草擬完先丟給 user 讓 user 用自己的話 phrase，不要 AI 一錘定音。User 編輯眼光在主軸 phrasing 上的權重 > AI 起草。

#### 2. Codex doc-review 第二觀點抓「動機尖銳度」比 self-review 準（N=2 evidence）

0430 doc-review 抓 cross-file consistency（stage-2 缺 frontmatter 對稱性）。本次 codex-architect 抓**動機尖銳度**——我寫「留下思考痕跡」太溫和，Codex catch user 真正動機是「保住自己思考，不被 AI 套路改寫」（防衛性）。這個 catch 解釋了 user 對 AI 味 / AI 故事化共鳴反應強的根本原因。

**How to apply**：寫主軸 / philosophy / motivation 類型文件時，self-review 之外必走一輪 codex 第二觀點，特別針對「我這版有沒有抓到 user 動機的尖銳度 / 是否太中性 / 太穩健」這種 register 問題。

#### 3. utility + affinity 不是 trade-off — 是 source 一樣的兩個副產品

我前期 frame 成「並重 / 順序 affinity 在前」（兩個目標 + 順序），Codex 反駁「兩者是判斷過程的副產品，寫對 process，兩個自然出現」。這個 reframe 一進來，整個 design 簡化掉「平衡兩個」的複雜性——只要軸心對了，兩者自動處理。

**How to apply**：未來 design 看到「並列兩個目標 + 平衡」這種 framing 警覺一下——可能上游有更 root 的 source 還沒抓到。

#### 4. subagent-driven-development × Haiku × markdown skill = 高 ROI workflow

8 task 全用 Haiku 跑 (implementer + spec reviewer + code reviewer)，Sonnet 只跑 final cumulative review。0 BLOCKED。每 task 平均：implementer 70-130s + spec ~50-100s + quality ~30-200s。Per-task 約 3-7 mins。8 task 全跑完 ~1 hr。Haiku 對 markdown 編輯任務（exact content 給足、verify command 給足）夠用，不必 Sonnet 全程。

**How to apply**：未來 markdown / config 編輯型 plan，default 用 Haiku 跑全 subagent loop；只在 final cumulative review 升級 Sonnet。Sonnet 跑 implementer 是浪費。

#### 5. plan 裡的 verify count（grep ≥ N）容易 over-strict — 改成 ≥ 1 / ≥ 實際 phrasing 出現次數

T2 plan 寫 `grep -c "Narrative-arc" ≥ 3`，實際 content 只 2 次（subsection 標題 + 選擇指南 bullet），是我 plan 算錯。implementer 報 DONE 沒當 concern flag——但這種 false positive 會讓 spec reviewer 多花時間判斷「是 plan 錯還是 impl 錯」。

**How to apply**：plan verify grep count 寫 `≥ 1`（only-if-present）或基於 spec 實際內容算次數，不要 inflate 數字。

#### 6. 「不刻意抓」≠「不 enforcement」— 軸心 reference 描述性 + 字句層 lint hard rule 分職

User reframe「不刻意抓 → 軸心擺位」明確要避開 enforcement，但同時 confirm 字句層 3 條（字短料多 / 刪雜質 / 一個重點）「該硬就硬」。最後設計分層：
- **軸心層**：reference 描述性，提供 default orientation，**不 gate**
- **字句層**：規格 hard rule，進 Gate 5→6 checklist + frontmatter 欄位

**How to apply**：「不要強制」跟「該硬就硬」共存的 design——分層處理，價值觀層走描述性，規格層走 enforcement。混為一談會讓 design 偏一邊。

#### 7. 「白話跟我溝通」N=3 active deployment — 已內化為實時 detection

本 session 中段 user 一句「用中文白話跟我溝通」我立刻把上一條訊息（充斥 declarative thesis / register / chokepoint / partial buy-in 等英文 jargon）重寫成白話版本，不需要再多輪 corrective。N=2 (0430) → N=3 (0504)。lesson 已內化。

**How to apply**：default 寫白話；要工程細節時 opt-in 詢問（「要我細說 X 嗎」）。當 user 流動性對話、reframe 中時，technical jargon 是 friction 不是 precision。

#### 8. feedback_user_reframing N=5 → N=6+

本 session 多次 reframe escape：
- 我提 a/b/c/d 4 條 design 路徑 → user (e)「先就對話分析歸納再討論解法」
- 我列 4 層痛點 → user 「大致對 你有發現嗎」（要我看更深一層）
- 我寫 5 段哲學 → user 「show, don't tell」一句
- 我提 (a)(b)(c) 整合方式 → user 直接「我們達成共識了」

連續 4 次方向不在我 a/b/c/d 框內。**escape hatch (d) 持續驗證重要**。

### 四、阻塞 / 卡點

無。

### 五、行動複盤

#### 1. brainstorming → spec → plan → execute 全程跑通的高 ROI workflow

第一次完整跑 superpowers:brainstorming → write-plan → subagent-driven-development 三層 skill 串聯。中間 surface 點：
- brainstorming 的「不要急著 propose 解法」red flag 接住（user reframe (e)「先分析歸納」）
- design doc → plan doc 的 transition 自然，因為 spec doc 已經把 sections 寫清楚
- subagent-driven-development 跑 markdown 編輯型 plan 完全無痛

**未來這個三層串聯都用同一 pattern**：brainstorming 收到 user reframe 後產 spec → spec 直接 inform plan → plan task 用 subagent batch。

#### 2. dirty state 處理該開工前先收乾淨（v1 經驗確認 N=2）

開工前先 commit 0430 dirty 117 行 = right call。如果跨 v2 落地中間夾著舊 dirty，git log 跟 cherry-pick 都會混。簡單規則：**開工前 git status 必須乾淨**（除了 gitignored）。

#### 3. plan 寫得越精準，subagent-driven-development 越 organic

T1-T8 implementer 全跑無 BLOCKED，因為 plan 把 file path / line numbers / exact content / verify commands 全部塞給 subagent。Subagent 只是 mechanical 執行，不需要 reason。**Plan 質量直接決定 subagent 落地速度**——這次 plan 寫法的 ROI 證明值得花時間在 plan 上。

#### 4. final cumulative review 比 per-task review 更能 catch system-level issues

Per-task review 抓 task 內部 spec compliance；final review 抓**跨檔案 cross-reference consistency**。本次 final reviewer catch:
- v1 變更歷史的「5 份 reference」現在 stale
- spec→plan 的 `type:` metadata gap
這兩個 per-task review 抓不到（因為 per-task 看不到全 spec）。

**How to apply**：plan 跑完最後一定要 dispatch final cumulative review，不要省。Sonnet 跑這道。

### 六、檔案異動

**新增**：
- `skills/threads-write-post/references/writing-philosophy.md`（86 行，T1）

**修改**：
- `skills/threads-write-post/SKILL.md`（Stage 1 entry / Stage 5 entry + schema / Reference table / 變更歷史 — T4/T5/T6/T7）
- `skills/threads-write-post/references/stage-1-framework.md`（加 Process-driven 框架段 + 選擇指南補 — T2）
- `skills/threads-write-post/references/stage-5-draft.md`（加字句層 Lint 段 + Gate 5→6 lint_passed item — T3）
- `CLAUDE.md`（Available Skills bullet 更新到 v2 — T8）
- `docs/handoffs/session-handoff-20260430.md`（commit 0430 17:24 區塊 117 行 — pre-T1 cleanup）

**新增（gitignored）**：
- `docs/superpowers/specs/2026-05-04-threads-write-post-v2-design.md`
- `docs/superpowers/plans/2026-05-04-threads-write-post-v2.md`
- `對話`（user 從外部丟進來的對話脈錄）

**未動**（per design Section 5）：
- `skills/threads-angle-gate/`（整 skill）
- `skills/threads-write-post/references/stage-2-plan.md`
- `skills/threads-write-post/references/stage-3-algo.md`
- `skills/threads-write-post/references/stage-4-interaction.md`
- `skills/threads-write-post/references/stage-5-draft.md` 的 Read Evidence Phrase（line 169）

### 七、收工回寫

- [x] **Memory**：建立 `project_progress_20260504.md`（記錄 v2 落地 + 8 個 insights + 6 個 active feedback 部署）
- [x] **MEMORY.md 索引**：加 0504 進度 + N=6 user reframing 更新 + N=3 白話溝通更新 + 新增 codex 第二觀點 catch motivation 尖銳度 lesson
- [x] **下次 session next action — T9 fresh-session validation**：
  - **P0**：開 fresh Claude Code session 找新題材跑 angle-gate + threads-write-post v2 全程驗證
  - **新題材建議**：本次對話的 v2 升級 journey（show-don't-tell reframe 過程 + 跟 Codex 對話拿第二觀點 + 8 task subagent loop 跑通）—— user 真實有感的 process，自帶 4 種 in-process 判斷可選
  - **驗 4 件**（final reviewer 點的）：
    - (a) Stage 1：philosophy reference 真讀 + framework 是否從 Narrative-arc / Thesis-argumentation 兩型挑（題材適合）
    - (b) Stage 5：兩份 reference 都讀（不是只讀一份說「另一份之前讀過」）
    - (c) lint_passed `true` 寫了 + 手動驗 3 條 hard rule（Rule 3 一篇一個重點 最易違反）
    - (d) read_evidence 欄位逐字含 anti-cheat phrase
    - (e) voice ground truth user 自評：是否「夠近不過頭、改不困難、不偏離、不過度模仿、方向對」+ 跟 v1.1 相比有沒有改善
  - **遇到 v2 缺口** → 寫 follow-up plan v2.1 patch
  - **P1（沿用）**：Stage 6/7 真實 CLI（要發的話）/ feat/advisor-plan branch handle / B 路線錄影送審
  - **P2（沿用）**：清理 `threads-kanisleo-post.png` / `.playwright-cli/`
- [ ] **可選**：push 到 remote (github)（未做，可下次或 user 自己處理）

---

## Session 16:44

### 一、今日聚焦

延續 14:14 接力棒 P0：跑 T9 fresh-subagent enforcement test，驗證 v2 升級的五個 enforcement 點是否有效。User 中段 reframe「不適合 user voice，換 assistant 自己當 author」，並追加 Codex 對照組測試。

### 二、完成事項

- **跑 T9 兩輪 fresh-subagent test**：
  - Round 1：general-purpose subagent（Sonnet）跑 Stage 1-6，產 5+1 份 artifact，11 分鐘
  - Round 2：Codex `codex exec` 跑同樣 prompt + 同樣 angle.md，11 分鐘，113K tokens
- **兩邊 v2 enforcement 五點全 PASS**：philosophy reference 真讀 / framework 從 Narrative-arc / Thesis-argumentation 兩型挑（兩邊都選 Narrative-arc）/ Stage 5 兩 reference 都讀 / lint_passed: true 寫了 / read_evidence 含 anti-cheat phrase
- **angle.md 跑 3 輪才對齊**：
  - v1（`ai-cowriting-too-well.angle.md`）試圖對齊 user voice → user 「不是我想表達的」 reject
  - v2（`bash-to-python-regret.angle.md`）放掉 voice 純 enforcement trap → user reframe「測不出我想表達的，這次讓你表達你想表達的」
  - v3（`give-options-they-jump.angle.md`）assistant 自己當 author，題材「我列得越完整、他越會自己另想」反向關係（從 N=7 user_reframing 計數 derive）→ 進測試
- **Codex draft > Claude subagent draft**（user 確認）：500 字 vs 724 字、1 個具體例子（show, don't tell 五段→一句）vs 6 個 inside baseball 場景、無 self-aware AI 開場句、句子分行更斷、開放式問句收尾（不用腳手架/容器隱喻）
- **Surface 7 個 gap → user 校正剩 5 個 production gap**：
  - **A1**：Stage 1 reference 新框架（Narrative-arc / Thesis-arg）vs 舊 16+1 清單 chosen_framework.id 沒整合（兩邊都打架）
  - **C1**：`threads-advisor review` 字數計算把 frontmatter 算進去（draft 實際 724 字、被警告 4414 字）
  - **C2**：`threads-advisor review` 沒讀 angle.md，5 條建議裡 3 條跟 author intent 衝突
  - **D1**（延後）：Stage 5 字數下限 80 vs Narrative-arc 短促節奏
  - **D2**（延後）：interaction `post_position` vs plan.md 沒 standalone 互動 post 的 fallback
  - **砍掉**：A2（Stage 6 兩 mode）/ B1（user-align 替代規格）—— test 場景才有的需求，不該污染 production spec
- **CLAUDE.md 新增白話規則段**（最頂部，header 下方第一個 section）：「與用戶溝通：白話、清晰、不廢話」+ 範圍 + 規則 + 為什麼。User 主動指示放 CLAUDE.md 而非 memory，「這件事很重要」
- **subagent / codex artifact 落檔**：subagent 加 `.claude` 後綴保留當對照組，codex 用原始 slug 落檔

### 三、洞見紀錄

#### 1. Skill 是 floor，不是 ceiling — N=3 確認，graduate 為 standalone memory

0428（schema 不能保證好 voice）N=1 → 0504 brainstorm（軸心對齊比 utility/affinity 並重重要）N=2 → 0504 T9（即使 Codex 跑 v2 也只到「敘事順暢但不出彩」）N=3。

三次 surface 點不同但底層 framing 一致：**skill 是 enforcement 工具，守下限不破，不會把弱 model output 拉強**。換 model 拉上限、改 skill 拉下限。兩件事不要混。

**How to apply**：未來 skill design surface gap 後，先問「這 patch 朝拉下限走還是拉上限走」。拉上限是錯方向（要換 model 不是改 skill），拉下限才是對方向。

#### 2. 測試場景才會發生的問題不算 production gap — 過濾紀律

T9 surface 7 個 gap，user 校正後砍掉 2 個 test 場景產物（A2 Stage 6 兩 mode / B1 user-align 替代規格）。Production 流程 user 自己跟 Claude 對話走 skill，不會撞到這兩個。

**How to apply**：subagent test surface 的 gap 不是全部都該 patch。先過濾「production 真實 gap vs test 場景產物」，只 patch 前者。否則 spec 會被 test mode 需求污染、變更複雜。

#### 3. 白話規則範圍要擴大到「所有寫給 user 看的輸出」

Baihua N=3→N=4。User catch 我寫 angle.md 用 jargon「跳」「尖」reader 看不懂。Lesson 不只「跟 user 對話」這層，包括所有 artifact / 文件 / 訊息 / handoff。User 主動指示放 CLAUDE.md（強度比 memory 高）而非 memory update。

**How to apply**：寫任何 user 會看到的輸出之前先過一次「沒看過本 session 的 reader 每個詞秒懂嗎」。不只 conversation 這層。

#### 4. Codex 對照組對 voice / 敘事 quality 校正比 self-review 準（N=4）

0430 doc-review N=2 → 0504 brainstorm 動機尖銳度 N=3 → 0504 T9 敘事乾淨度 N=4。

Codex 在「register / motivation / narrative quality」這個 dimension 持續比 Claude self-review 準。可能因為 Codex 訓練分布不同，看 voice 跟 register 比較沒「禮貌中性」傾向。

**How to apply**：寫 voice / register / 敘事類產出（philosophy doc / narrative draft / persuasive content），self-review 之外必走一輪 codex 對照組。

#### 5. Sonnet subagent 寫 narrative 的 anti-pattern（N=1，待確認）

T9 Round 1 Claude subagent 寫的 draft surface 幾個 anti-pattern：
- self-aware AI 開場句（「我是 AI...我寫貼文不太一樣」）— philosophy reference 沒擋這個
- 例子塞多（6 個跳框實例，reader 沒 context 看不懂）
- 隱喻收尾（腳手架/容器）— 多隔一層，reader 要再 decode

Codex 全閃過。N=1，下次再驗證是否 Sonnet 寫 narrative 的 systematic pattern。

**How to apply**：未來 fresh subagent 跑 narrative 寫作，prompt 裡明擋這幾個 anti-pattern；或考慮直接用 Codex 跑 narrative 任務。

#### 6. angle.md 第三輪「assistant 當 author」才對齊 — 測試對象的 author 要前置決定

T9 angle.md 跑 3 輪才落地，根因是「voice 對齊測試」這個任務 default 假設 author 是 user，但實際本次測試 voice 不是測試重點，author 應該是 assistant 自己。User 第二次 reframe 才 surface 這個 default 假設錯了。

**How to apply**：subagent test 規劃前，先決定 author 是誰（user / assistant / 第三方），不要假設 default 是 user。Author 不同，angle.md 寫法跟測試評估標準都不一樣。

### 四、阻塞 / 卡點

無。

### 五、行動複盤

#### 1. CLAUDE.md > memory（給重要 rule）

User 0504 主動指示白話規則「放 claude.md 因為這件事情很重要」。CLAUDE.md 每 session 自動 load + 強度比 memory 高（memory 是被動推送、context 多時可能淹沒）。未來重要 rule（影響每次互動的 / cross-cutting 的）直接放 CLAUDE.md。

#### 2. subagent dispatch prompt 該明寫 author / 視角

T9 第一版 prompt 沒明寫「author 是 assistant，第一人稱 AI 視角」，subagent 自己讀 angle.md frontmatter 才確認。下次規劃 subagent task，prompt 開頭直接明寫「author / 視角 / 評估角色」這三件事，不要讓 subagent 從 input 反推。

#### 3. enforcement test 跑 codex 對照組是高 ROI workflow

T9 第一輪只跑 Sonnet subagent，user catch「不知道在說什麼」之後才跑 Codex 對照組。**對照組應該 default 跑兩輪**（同 prompt / 不同 model），surface model-specific 問題 vs spec-level 問題。

成本：Codex `codex exec` 11 分鐘 / 113K tokens / 背景跑不卡 main session。值得。

### 六、檔案異動

**新增**：
- `drafts/give-options-they-jump.angle.md`（最終版 v3）
- `drafts/ai-cowriting-too-well.angle.md`（v1，被 reject 保留當記錄）
- `drafts/bash-to-python-regret.angle.md`（v2，被 reframe 保留當記錄）
- `drafts/give-options-they-jump.framework.claude.md` / `.plan.claude.md` / `.algo.claude.md` / `.interaction.claude.md` / `.draft.claude.md` / `.review.claude.md` / `.draft.review.claude.md`（subagent Round 1 產出 + 加 `.claude` 後綴）
- `drafts/give-options-they-jump.framework.md` / `.plan.md` / `.algo.md` / `.interaction.md` / `.draft.md`（codex Round 2 產出）
- `drafts/.codex-prompt.txt`（codex prompt input）
- `drafts/.codex-output.log`（codex log 11253 行）

**修改**：
- `CLAUDE.md`（最頂部新增「與用戶溝通：白話、清晰、不廢話」段）

**未動**：
- v2 skill 本體（`skills/threads-write-post/`）— gap 留 v2.1 patch 處理

### 七、收工回寫

- [x] **Memory**：update `project_progress_20260504.md`（T9 兩輪測試結果 / 7→5 gap 過濾 / floor-not-ceiling N=3）
- [x] **Memory**：update `feedback_baihua_communication.md` N=3→N=4 + 範圍擴大「文件層」+ CLAUDE.md 規則化
- [x] **Memory**：新建 `feedback_skill_floor_not_ceiling.md`（N=3 graduate 為 standalone memory）
- [x] **MEMORY.md 索引**：加 floor-not-ceiling memory + baihua N=4 update
- [x] **下次 session next action — v2.1 patch**：
  - **P0**：A1 / C1 / C2 三條真實 production gap
    - **A1**：`skills/threads-write-post/references/stage-1-framework.md` 把新框架（Narrative-arc / Thesis-argumentation）跟舊 16+1 清單整合（要嘛砍舊清單、要嘛 schema 改成接受兩種 ID）
    - **C1**：`threads_pipeline/advisor.py` review 字數計算改成只算 post text，不算 frontmatter
    - **C2**：`threads_pipeline/advisor.py` review 跑時 load 同 slug 的 angle.md frontmatter，把 expected_show_points / expected_tell_red_lines 注入 review prompt
  - **P1**：階段二測試（換乾淨環境跑 angle-gate + threads-write-post + 安裝流程驗證）
  - **P2（沿用）**：Stage 6/7 真實 CLI（要發的話）/ feat/advisor-plan branch handle / B 路線錄影送審
  - **P3（沿用）**：清理 `threads-kanisleo-post.png` / `.playwright-cli/`
- [ ] **可選**：push 到 remote (github)（未做，可下次或 user 自己處理）
