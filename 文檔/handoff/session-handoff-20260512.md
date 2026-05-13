# Session Handoff — 2026-05-12

## Session 09:23

### 一、今日聚焦

接續 0511 跨日（從 0511 早上 09:00 v3.0.1 merge 完之後、下午轉到「角色定位 + 內核」深度討論、跨夜到 0512 早上）── 落地 v3 缺的「**用戶角色設定資料**」這一層 Layer 1，並對 v3 整合提出設計筆記。

### 二、完成事項

**A. 整理 repo（0511 接續）**
- 移 3 個中文檔到 `docs/dev/{notes/,}`：對話 / 練習的過程 / 討論
- 4 個 temp / probe artifact 進 `.archive/`：codex-prompt / tmp-claude-step7 / openspec test-default-schema / threads-kanisleo-post.png
- 3 個 commit 落地 + push origin/main：
  - `bd7894f` CLAUDE.md 白話規則段
  - `401963e` 5 份 handoff（補 0504 + 新 0505/06/08/11）
  - `a75ad15` 散落筆記移到 docs/dev/

**B. 跟 user 跨日 explore「角色定位」概念**
- 從 5/8 acceptance 痛點 vs 5/9 SEO 月報順 直接對比 surface「角色定位」這層 v3 缺口
- 識別 **3-layer 模型**：內核（固定）/ 角色設定（每篇變）/ 文風（自然 derive）
- 從 user 10 篇 Threads 文章 surface **4 種常用角色樣子**（A 從接觸新領域到做出成果者 / B 行動派 builder / C 思想評論者 / D 父親+反思者）
- 跟 user 走過 13 項 framework 收完：**內核 9 條 + 紅線 8 條 + 受眾 ABC + 表達偏好 + 草稿品質下限**
- user 補強 framing：5/9 SEO 月報是體悟「**先訂角色、後面才不會偏調**」的起點

**C. 落地 2 份 artifact**
- `skills/threads-write-flow/references/02-user-profile.md` ── Layer 1 用戶角色設定資料（跟 00-philosophy / 01-user-expression 並列為基底 ref、按需載入）
- `docs/dev/2026-05-11-user-profile-v3-integration-design.md` ── v3 整合設計筆記（對位 5/8 痛點、列每個 step 該動什麼、P0/P1/P2 優先序、不寫 code）

**D. profile.md 8 sections 全 verify、修了 5 處**
1. 1.4 拿掉外部工具（superpowers / sd0x-dev-flow / openspec）── user catch「那是工具不是開發項目」
2. 內核 #7 reframe「**主動學習 / 自我提升 / 願意克服挑戰**」── user catch 我又滑回「新手」被動 framing
3. 6.2 紅線描述簡化
4. 6.3 縮一行 reference 不重複（已在 00-philosophy）
5. 樣子 A 跟 arc 範例同步去掉「新手」

### 三、洞見紀錄

#### 1. 「角色定位」≠ user voice ── 是把文章中的「我」當可塑造角色

User 0512 surface 的核心發現：「不同題材 / 場景 / 任務、我的角色不一樣、文筆用詞切入點也不一樣」。深一層 ── 角色設定 = 故事 / 文章中角色的設定（身份 / 視角 / 思維 / 背景 4 維）、設定好之後才能在段落內推「角色變化 + 起承轉合」。題材沒明顯 arc 也 OK ── 但設定本身讓「文章中的我」對讀者清楚。

#### 2. 5/8 vs 5/9 對比是「角色定位」洞察的 ground truth

5/8 acceptance：開頭「謝謝 AI」、預設「AI 受惠者」角色、5 輪 reframe 都在拉。5/9 published（SEO 月報）：開頭「一年前剛接觸行銷的我」、user 主動下角色設定、整篇順、上 Threads 沒大改。**同題材、同 user、相隔 1 天、結果截然不同**。差別在角色預設誰是主體。

#### 3. 內核「主動學習」反 framing ── N=2 graduate

User 0510 confirm「我願意接觸新的領域、並從中學習」、不是「平庸的初學者」；0512 verify Section 4 又 catch 我把樣子 A 寫成「從新手成長到成果者」── 同一個 framing 滑兩次。教訓：被動 framing（新手 / 初學者 / 受惠者）對 user 是地雷、寫任何描述前先問「主動 or 被動」。

#### 4. 草稿品質下限 = 「user 不需要從頭重寫」

不是「user 不想改」── 改是預期、line-edit 是常態。紅線是「foundational 沒對齊、user 要從頭重寫」。對應到「skill = floor」N=2 ── floor 守的是「不讓 agent 寫出不能用的東西」。

#### 5. 訪談 + 刪除法 N=10+ 用得很順

整個 session user 1-2 字回應推進：「A」「對」「3 是這個」「就先這樣吧」── surface + 給選項 + 刪除法 模式 N 持續累積。違反訊號：(11)-(13) 我列抽象問題、user catch「你怎麼會列成這樣」── 我違反「沒有就沒有」過度引出。

### 四、阻塞 / 卡點

- **profile 揭露程度（Thread A）尚未 settle**：軍人背景 leak 到 public repo（threads_pipeline 已 push GitHub）── 4 個處理方式給 user 刪除法、user 還沒 decide
- **Thread B / C / E 還沒走**：4 維 vs 4 樣子關係釐清 / 載入時機 / memory 重複度

### 五、行動複盤

#### 1. profile.md 一段一段 verify 模式效率高

8 sections 用「我顯示原文、user 1 行回應對 / 漏 / 不對」── user 接受度好、修正快。下次寫 reference 文件 verify 也用這模式。

#### 2. 又滑回「新手」被動 framing 兩次

0510 user 第一次 reframe、0512 內核 #7 + 樣子 A 又滑兩次。**同 session 已 catch 過的 framing 還會再犯** ── 教訓是寫描述前先 grep 一次「新手 / 初學者 / 受惠者」這類詞、提前 reframe。可考慮加 lint。

#### 3. (11)-(13) 抽象問題違反「沒有就沒有」

寫了「個人觀察 / 經驗 / 信念」3 項、其實前面 framework 已 cover。user catch「你怎麼會列成這樣」── 我硬擠第三層、應該停。下次 surface「還缺什麼」之前先 self-check「前面 framework 是不是已 cover 了」。

### 六、檔案異動

- **新增**：`skills/threads-write-flow/references/02-user-profile.md`（用戶角色設定資料 / Layer 1）
- **新增**：`docs/dev/2026-05-11-user-profile-v3-integration-design.md`（v3 整合設計筆記）
- **commit + push to origin/main**：3 個 commit（CLAUDE.md / 5 handoff / 散落筆記）── ba606e6 → a75ad15
- **整理**：3 中文檔搬 docs/dev/{notes/,}、4 temp 進 .archive/
- **空目錄**：`docs/user/` 空殼留著（git 不追蹤）

### 七、收工回寫

- [x] **memory**：建立 `memory/project_progress_20260512.md`（記角色定位深度討論 + profile.md / design notes 落地）
- [x] **MEMORY.md**：索引同步 0512 entry
- [x] **Thread A（揭露程度）settle 在 option 3**：profile.md gitignored、template.md 公開範本、`.gitignore` 加規則、design notes 同步
- [x] **Thread B（4 維 vs 4 樣子關係）settle**：Section 7 重寫 ── 拆 7.1 4 維 schema + 7.2 樣子實例（條列格式取代表格、agent 更好讀）；template.md 同步
- [x] **Thread C（載入時機）settle 在 option 3**：Step 1 全載 baseline + Step 2/3/5/8 按需 reread 相關 section（design notes 加 per-step reread 表、迭代規則「先落地測試再調整」）
- [x] **Thread E（跟 memory 重複度）settle 在 option 1**：兩邊保留 + cross-reference；audience 不同（memory 跨專案 / profile 寫作 specific）；4 樣子 / 4 維 / 8 紅線是 memory 沒 codify 的新 layer
- [ ] **下次 session next action**：
  - **P0**：開 OpenSpec propose v3.1 patch、把 Step 1/2/2.5/3 改動正式落地（design notes 已就緒）
  - **P1**：「討論議題」歸檔（外部 AI 寫的優化規格、本次 explore trigger 素材、本地未處理 ── 4 個選項 a/b/c/d 給 user）
  - **P2**：SKILL.md 加 setup 步驟說明（template.md → 02-user-profile.md copy + fill），讓未來 user 知道怎麼用
