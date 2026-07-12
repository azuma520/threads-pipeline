# Session Handoff — 2026-04-22

> 本檔為當日 append-only 工作紀錄。每個 session 結束時加一個 `## Session HH:MM` 區塊，**禁止修改前面 session 的內容**。

---

## Session 08:30

### 一、今日聚焦

- GA4 電商漏斗 bug 修復複盤（上午、非 threads_pipeline 專案範圍）
- AK-Threads-booster 對照研究 + AI 生草稿 C 路線設計（主線）

### 二、完成事項

**A. GA4 複盤討論（session 前段）**

- 用戶帶完整複盤進場（v31 → v32 修復，附三層行為審查框架）
- 我補兩點觀察：
  - 「修復後每次 click 2 次 /collect」計畫等真實訂單驗證 → 這正是被診斷為反模式的「等真實訂單」模式；建議現在就 click 5 次用 Realtime 驗證
  - 三層審查框架對這次 bug 只有「驗證層」真的會攔下；對照層/範圍層在 4-17 當時救不了
- 用戶想寫成 Threads 貼文；我給了 270 字草稿（未發）

**B. 下載 AK-Threads-booster + 初步對照**

- Clone 到 `.reference/AK-Threads-booster/`（不進 git）
- Dispatch Explore agent 做全面對照研究
- 識別 3 個候選加強點（按 value/effort 排）：
  - #1 Semantic Freshness Gate（小 / 高）
  - #2 AI-tone Detection（中 / 高）
  - #3 Review → Tracker 迴路（大 / 最大）
- 產出：`docs/dev/ak-threads-booster-research.md`（新檔，untracked）

**C. 候選 #1 深入研究**

- 讀 AK 的 `skills/draft/SKILL.md`、`skills/topics/SKILL.md`、`scripts/update_topic_freshness.py`
- 校正：Freshness Gate 是**兩個正交系統**（自我重複偵測 + 外部飽和度檢查）
- 發現 `advisor.py:97-102` 的 `freshness_status` 只是天數、不是語意
- 確認架構方向（Q1-Q4 決定）：
  - Q1 運算時機 → **方案 C**（簡化即時版，SQL 拉近 N 天 → Python 算 → 不寫回 DB）
  - Q2 外部飽和度 → **暫緩**（等 API 權限或 WebSearch 通道）
  - Q3 Jaccard + n-gram 對繁中誤群風險 → **動工前必做 PoC 驗證**
  - Q4 Gate 強度 → **打分數不硬擋**
- 討論「用資料庫做相似度」：結論是資料留 SQLite、Python 算，不走 FTS5 / vector embedding

**D. 挖出 feat/advisor-plan 分支 + 4-14 翻車診斷**

- 用戶提「有個指令機制」→ 查出 `feat/advisor-plan` branch（24 commits ahead, PR #1 open, 8 天未 merge）
- `planner.py` 兩階段 AI 生骨架（Stage 1 選框架 → Stage 2 產串文每則鉤子/字數/情緒）
- 讀 `docs/superpowers/handoffs/2026-04-14b-threads-advisor-step5-fail.md`
- 確認卡在實戰失敗（用戶語：「學得太過分了」「一點都沒有創意」），不是技術問題
- 當晚三個診斷（A. voice-patterns 被當必撒清單 / B. 缺語氣錨點 / C. 缺選角度步驟）

**E. 路線選擇：AI 生草稿 C 路線**

- A/B/C 三路線討論，選 C（AI 生骨架 + 人填內容 + AI 防味）
- 排除 A（AI 從零寫）：短期達不到用戶的人工標準
- 校準：AI 草稿常態是「還不錯需要修」，4-14 是特例不是通則
- 4 層藍圖確定：
  - 1. 選角度 Gate（新增 / AK 無 / A 級）
  - 2. 生骨架（已有 planner.py / 待 merge + 角度輸入升級）
  - 3. 填內文（人寫、工具輔助）
  - 4. AI 防味（從 AK 借 + cosplay 檢測客製）

**F. 基礎建設改進**

- 用戶指出：沒養成寫 `project_progress_YYYYMMDD.md` 的習慣
- 補寫 `memory/project_progress_20260422.md`
- 參考 SEO workspace 的 session-handoff + hook 機制
- 建立 `docs/handoffs/` 資料夾 + 本 handoff 檔
- 在 `.claude/settings.local.json` 新增 SessionStart + Stop hooks（保留原 28 條 permissions）
- 在 `CLAUDE.md` 新增「Session 開工規則」「Handoff 格式」「記憶系統與 handoff 的分工」三段
- 自我驗證：7 欄 grep 全 OK、JSON 解析通過

### 三、洞見紀錄

- **AK 的 Freshness Gate 是兩個正交系統、不是一個**：第一次對照講成一個東西，仔細讀 `update_topic_freshness.py` 才發現 System A（自我重複離線群聚）跟 System B（外部飽和度即時 WebSearch）是獨立機制，catch 的是不同 failure mode。**下次做類似功能對照要先拆底層機制、再講抽象概念**。
- **用戶的品質標準是人工水位**：「我現有貼文都很喜歡」這句話隱含「我的好 = 手寫標準」。AI 生草稿對他而言不是 A 路（AI 從零寫）可行，必須是 C 路（工具輔助流程、人寫內文）。先前推薦吸收 AK 時如果沒做這個區分會方向錯。
- **4-14 的根本失敗不是「AI 不夠好」**：是「沒有強迫使用者想清楚就動筆」。工具補的是「問出銳利點」這步，不是「寫出好文字」這步。這個認知會影響整個 C 路線的第 1 層設計（選角度 Gate 要做成蘇格拉底 gate、不是產角度的工具）。
- **元：我這次 session 漏寫工作紀錄**。只更新 research doc + memory 指針，沒建 `project_progress_YYYYMMDD.md`，也沒建 handoff 檔。用戶場上指出。下次應該：session 一有實質進展就建檔，不靠「研究文檔夾帶」。

### 四、阻塞/卡點

- 選角度 Gate 的具體形式（互動 CLI / 批次 / skill step）未決
- 「角度 Gate」強度（硬擋 vs 建議）未決
- feat/advisor-plan branch 的處理（merge 先 / 升級後 merge）未決
- 候選 #1 的 PoC（誤群風險驗證）未跑

### 五、行動複盤

- **偵錯順序穩**：GA4 那段用戶帶完整複盤進場，我針對「等真實訂單驗證」再次踩到同反模式這點明確指出，對話方向立刻收斂
- **討論節奏健康**：AK 對照研究從「點對點吸收」擴展到「整體架構」是用戶一句話（`AI 生草稿是我們的目標`）引導的；我沒護航前面的判斷，直接重新 frame，避免強推錯誤方向
- **應改**：研究進行途中應該**更早**建 handoff 檔。這次等用戶指出才補，等於前 4 小時工作沒進工作紀錄
- **觀察**：今天話題廣（GA4 / AK / C 路線 / infra），如果沒寫 handoff 下次開 session 要重新拼 context 會非常痛

### 六、檔案異動

**新增**：
- `.reference/AK-Threads-booster/`（clone，.gitignore 已排除）
- `docs/dev/ak-threads-booster-research.md`（研究文檔，~1500 行，untracked）
- `docs/handoffs/`（新資料夾）+ `docs/handoffs/session-handoff-20260422.md`（本檔）
- `memory/project_progress_20260422.md`（memory 進度）
- `memory/project_ak_threads_booster_compare.md`（memory 指針，待下次 session 讀）

**修改**：
- `memory/MEMORY.md`（新增兩條索引）
- `.claude/settings.local.json`（新增 SessionStart + Stop hooks，permissions 保留）
- `CLAUDE.md`（新增 Session 開工規則 / Handoff 格式 / 記憶系統分工 三段）

**未動**：
- `advisor.py` / `planner.py` / `insights_tracker.py` 等核心程式碼：本次完全未修改
- `feat/advisor-plan` branch：狀態維持 PR #1 open，未 merge

### 七、收工回寫

- [x] `memory/project_progress_20260422.md` 已建
- [x] `memory/MEMORY.md` 索引已更新（新增 04-22 進度 + AK 對照指針）
- [x] `memory/project_ak_threads_booster_compare.md` 指針檔存在且指向研究文檔
- [x] `.claude/settings.local.json` hooks 已設（SessionStart + Stop，自我驗證通過）
- [x] `CLAUDE.md` Session 規則三段已加
- [ ] **下次開工 next action（接力棒）**：二選一
  - A. 跑候選 #1 的 PoC — 把 SQLite 貼文匯出成 AK tracker.json 格式、跑 `update_topic_freshness.py`、看繁中 AI/tech 內容有無誤群
  - B. 繼續挖選角度 Gate 設計 — 決定形式（互動 CLI / 批次 / skill step）+ 強度（硬擋 vs 建議）
- [ ] 開工前先確認上述兩個選項哪個優先（用戶決定）
