# Session Handoff — 2026-04-24

> 本檔為當日 append-only 工作紀錄。每個 session 結束時加一個 `## Session HH:MM` 區塊，**禁止修改前面 session 的內容**。

---

## Session 08:07

### 一、今日聚焦

- 開工接力：決定今天走哪條主線（A/B/C 三選一，定義見 `session-handoff-20260423.md` Session 18:07 最末）
- 先把昨晚（0423 18:07）未落檔的 Playwright 探索設計 append 到昨天的 handoff

### 二、完成事項

- 讀完昨日最新 handoff 狀態：17:18 → 17:59 → 18:07 三段推進已知
- 將 0423 18:07 「Playwright + embedded Relay JSON 探索」完整區塊 append 到 `session-handoff-20260423.md`（~170 行）
- 建立今日 handoff 檔案（本檔）

### 三、洞見紀錄

- **跨日 session 的 handoff 歸屬**：昨晚 17:30 起的探索對話跨過午夜，Stop hook 觸發在 0424 早上——這種情境下正確做法是「工作內容寫進實際發生日的 handoff（0423 18:07）」+「跨過去當天也要建 handoff 捕捉當日動作（0424 本檔）」。規則上就是「每日一檔」，不因 session 連續而合併。

### 四、阻塞/卡點

- **今日主線待使用者拍板**（3 選 1）：
  - **A**：實作 `scripts/fetch_threads_post.py`（昨晚 18:07 設計延續）
  - **B**：錄 `profile_discovery.mp4` + Stage 5 送審（17:59 接力棒）
  - **C**：寫 `threads-angle-gate` skill 草案（17:03 接力棒）

### 五、行動複盤

- 無（本 session 到目前為止只做接力交接，尚無實作動作可複盤）

### 六、檔案異動

**新增**：
- `docs/handoffs/session-handoff-20260424.md`（本檔）

**修改**：
- `docs/handoffs/session-handoff-20260423.md`（append Session 18:07 區塊）

**未動**：
- 所有代碼
- memory 所有檔案（等主線確定再動）
- `threads-kanisleo-post.png` 與 `.playwright-cli/`（待清理，等 A/B/C 決策後一起處理）

### 七、收工回寫

- [x] 0423 18:07 區塊已補齊（Playwright 探索設計定稿）
- [x] 今日 handoff 已建（本檔）
- [ ] **下次 session next action（linear）**：
  - **P0**. 使用者拍板今日主線（A/B/C）
  - **P1**. 依決策選定主控文檔讀取：
    - A → `docs/handoffs/session-handoff-20260423.md` Session 18:07
    - B → `docs/app-review/resubmission-plan.md` + `demo-script-profile-discovery.md` Plan B 段
    - C → `docs/dev/ak-threads-booster-research.md` 第 1 層定稿章節
  - **P2**. 清理 `threads-kanisleo-post.png` 與 `.playwright-cli/`（無論走 A/B/C 都要做）
- [ ] 主控文檔 SSOT 清單：
  - App Review：`docs/app-review/resubmission-plan.md`
  - C 路線：`docs/dev/ak-threads-booster-research.md`
  - Playwright 探索（昨晚新增）：`docs/handoffs/session-handoff-20260423.md` Session 18:07（尚未晉升為獨立 SSOT，等實作時再建）

---

## Session 08:21

### 一、今日聚焦

- **主線拍板：C 路線第 1 層落地**——寫 `threads-angle-gate` skill 草案

### 二、完成事項

- 讀 `docs/dev/ak-threads-booster-research.md` v6 第 1 層定稿（701 行）吸收設計要素
- 寫 `skills/threads-angle-gate/SKILL.md` 草案（253 行 / 751 字），覆蓋：
  - 訪談者+共創者角色定位
  - 鐵律（只有「發問」和「總結+詢問」兩種發言形式）
  - 雙向萃取 + 三種 source label（`user_material` / `ai_observation` / `co_created`）
  - 共鳴的操作化（問答迴路收斂到使用者點頭）
  - 內部四透鏡不對外
  - Override 路徑
  - `drafts/<slug>.angle.md` 產出格式
  - Red flags 表 + rationalization 表
- 跑 RED-GREEN-REFACTOR 驗證：
  - **RED (baseline 無 skill)**：結尾產生兩句 soft-assertion 下定論（「最有張力的不是 X 而是 Y」「這是 X 的故事，不是 Y 的故事」），正是 4-14 翻車模式
  - **GREEN v1 (skill loaded)**：自己 self-critique 抓到兩個 borderline 違規——Turn 1 拋 3 個 numbered questions（問卷感） + 觀察沒用明示 phrase 標 source
  - **REFACTOR**：加三個小節 + 兩條 red flag 關 loophole：
    - 「Soft-assertion 也是違規」（「我覺得 / 直覺 / 最有張力的是」包裝仍是斷言）
    - 「Turn 1 的節奏：一題，不是問卷」
    - Source label 必須用的 phrase 表（明示 phrase vs 軟性 framing 反例）
    - 「句號改問號唸一次」自檢法
  - **GREEN v2 (refactor 後)**：四條強化規則全 PASS，Turn 1 只問一題、用「我從你剛才講的」明示標 source、無任何斷言
- 更新 `CLAUDE.md` Available Skills 段落加入 `threads-angle-gate`

### 三、洞見紀錄

- **Baseline Claude 的 soft-assertion 盲點**：不帶 skill 的情況下，Claude 會用「我覺得」「直覺」「丟個觀察給你」把斷言包裝起來，自己覺得是「有分寸」但其實違反 v6 鐵律。這類 soft-assertion 比 hard-assertion 更難偵測，所以 skill 必須**明示**禁止。
- **Source label 要 phrase-level enforcement**：光說「要標 source」不夠，Claude 會用「聽起來 X」「感覺上 X」這種軟性 framing 自以為標了——必須給明示 phrase 清單 + 反例表才擋得住。
- **Turn 1 節奏是獨立紅線**：「不要 menu 3 個角度」跟「不要 Turn 1 問 3 題」是兩回事。前者已經在 v6 設計中，後者是測試才暴露的，要獨立加一條。
- **「句號改問號唸一次」自檢法有效**：給 Claude 一個可自檢的機械 rule，比要求它「有訪談者氣質」更管用。這個模式可以推廣到其他 discipline-enforcing skill。

### 四、阻塞/卡點

- 無

### 五、行動複盤

- **TDD for docs 真的會抓到盲點**：原本打算「設計定稿就直接寫 skill 收工」，baseline 測試出來暴露 soft-assertion 違規、GREEN v1 又抓出 2 個 borderline，總共補 3 條強化規則——沒做 RED-GREEN-REFACTOR 這三條都不會存在。
- **草案不等於半成品**：使用者說「寫草案」但產出通過 2 輪測試，實質上可以直接使用。下次「草案」任務要早點跑測試，不要等「正式版」才測。

### 六、檔案異動

**新增**：
- `skills/threads-angle-gate/SKILL.md`（253 行，v6 第 1 層落地草案）

**修改**：
- `CLAUDE.md`（Available Skills 段落加一行）
- `docs/handoffs/session-handoff-20260424.md`（本區塊）
- `docs/dev/ak-threads-booster-research.md`（第 1 層「仍待決」第 1 項標 ✅，末尾加指向 roadmap 的 pointer）

**新增（audit 後）**：
- `docs/dev/threads-angle-gate-roadmap.md`（skill-creator audit 產出的優化 roadmap；P1 存 evals.json / P2 拆 template / P3 description 風格張力 + 實測後可能浮現的待辦）

**未動**：
- `docs/dev/ak-threads-booster-research.md`（SSOT，第 1 層設計未變）
- 代碼（純 skill，零代碼）
- `threads-kanisleo-post.png` / `.playwright-cli/`（P2 清理待辦，仍未處理）

### 七、收工回寫

- [x] Memory 建立：`project_progress_20260424.md`（本 session 完成）
- [x] `MEMORY.md` 索引同步（加 0424 條目）
- [x] **兩個 commit 上 origin/main**：
  - `1f45974` feat(skills): add threads-angle-gate skill
  - `f47bcdb` docs(dev): threads-angle-gate optimization roadmap + session handoff
  - 走 PR #3（feat/fetch-threads-post → main），含本 session + 另一個 shell 的 Playwright prototype 共 6 commits，已 merge（main tip `2047715`）
  - PR #1（feat/advisor-plan）仍照決策 B 保持 open，等 C 路線全層想清楚再動
- [ ] **下次 session next action（linear）**：
  - **P0**. 實測 `threads-angle-gate` skill：找一個真實要發的題目走一遍，看對話體感如何；可能需要再 refactor
  - **P1**. 選做（3 選 1）：
    - 繼續 C 路線：第 2 層 `planner.py` 升級（讀 angle.md 生骨架），或先 merge `feat/advisor-plan`
    - 切 App Review B：錄 `profile_discovery.mp4` + Stage 5 送審
    - 切 A 路線：`scripts/fetch_threads_post.py` 實作
  - **P2**. 清理 `threads-kanisleo-post.png` 與 `.playwright-cli/`（持續待辦）
- [x] 主控文檔 SSOT 清單（此 session 不變）：
  - App Review：`docs/app-review/resubmission-plan.md`
  - C 路線：`docs/dev/ak-threads-booster-research.md`
  - **新增** C 路線第 1 層 skill：`skills/threads-angle-gate/SKILL.md`

---

## Session 13:15

### 一、今日聚焦

- 主線 A：`scripts/fetch_threads_post.py` prototype 實作（0423 18:07 Playwright + Relay JSON 設計落地）
- 全程走 superpowers 機制：writing-plans → review-spec（第三方審查 2 輪）→ subagent-driven-development → finishing-a-development-branch

### 二、完成事項

- 寫計畫 `docs/superpowers/plans/2026-04-24-fetch-threads-post.md`（~1200 行，11 Task TDD）
- **第三方審查 2 輪**（`sd0x-dev-flow:review-spec` / tech-spec-reviewer subagent）：
  - Revision 0→1：修 B1（meta 肥大）+ I1（walk_posts 假陽性）+ I2（真 fixture anchor）+ I3（regex 屬性序）+ I4（extract 失敗 debug dump）+ I5（classify 缺欄位語義）+ N1/N3/N4 cosmetic
  - Revision 1 re-review：**Approved** + 3 個 cosmetic fix
- **Subagent-driven 執行**（11 subagent 派發：10 implementer + 4 spec-reviewer）：
  - Task 0 setup + fixture（抓 `@kanisleo328/post/DXO2PlPEoOQ` 真 Relay payload，78KB）
  - Task 1–9：parse_url / classify / walk_posts / extract_relay_json / filter_by_flags / render_markdown / write_output / fetch_page / main orchestrator
  - Task 10：真 URL end-to-end smoke
- **產出**：
  - `scripts/fetch_threads_post.py`（~180 行）
  - `tests/test_fetch_threads_post.py`（37 tests）
  - `tests/fixtures/relay_kanisleo_DXO2PlPEoOQ.json`（78KB schema-drift regression anchor）
- **全 repo 264 tests 綠**（baseline 227 + 新 37）
- **End-to-end smoke**：真 URL counts `{A:1, B:1, C:4, D:6, E:0}` = 12（handoff 0423 18:07-D 精確命中），`--include-replies` [D] 0→6、URL 解析錯 → exit 1、I4 debug dump 手動觸發驗 marker 還原
- **12 commits 上 origin/feat/fetch-threads-post + PR #4 建立**：https://github.com/azuma520/threads-pipeline/pull/4

### 三、洞見紀錄

- **「計畫的 schema 假設」必須實測驗證**：原計畫依 0423 18:07-C 假設 `is_reply` 在 post root，Task 0 subagent 抓真 fixture 實測發現巢在 `post["text_post_app_info"]`。純合成測試不會抓到欄位巢狀錯誤——**真 fixture anchor 是必要投資**。
- **「第一個含 marker 的 script」是 SSR SPA 的常見陷阱**：Meta Threads 頁面 7 支 data-sjs 都含 `BarcelonaPostPageDirectQuery`，只 1 支真含貼文 records（其他是 query 定義 / cache reference / metadata）。選擇邏輯必須走語義（對所有 candidate 跑 `walk_posts` 計數取最大），不能走詞法匹配（first hit）。此經驗可通用到抓其他 React/Next.js SSR 頁面。
- **Subagent-driven two-stage review > inline 實作**：fresh context per Task、implementer 不會自證、reviewer 獨立驗 git log + 跑 pytest + runtime assert。例 Task 3 reviewer 自己跑 `all("pk" in p for p in posts)` 驗 guard 真生效——這層我自己跑過可能漏。
- **第三方審查是便宜高 leverage 投資**：2 輪 tech-spec review ≈ 20 分鐘，抓到 1 Blocker + 5 Improvements，省了至少兩次大重構。
- **實測發現 schema 漏洞時正確做法**：「改計畫 → 再派 subagent」不是「直接 in-place 修代碼」。Task 0 subagent 正確 BLOCKED + 提供 diagnostic，我更新計畫（walk guard `is_reply` → `pk`、classify 改讀巢狀）再派第 3 subagent 才順利。保持計畫為 SSOT。
- **Pyright stale hints 在 TDD 漸進檔常見**：`import json` / `import pathlib` / `import argparse` 分 Task 加入時 Pyright 報 "not accessed"，後續 Task 才消化——收 diagnostic 要看上下文，不無腦修。

### 四、阻塞/卡點

- 無

### 五、行動複盤

- **superpowers 全流程跑一次值得**：writing-plans + 2 輪審查 + subagent-driven + finishing 全走完約 3–4 小時，但省了至少兩次大重構（B1 meta 肥大 / walk_posts 假陽性 / schema 巢狀都會在執行後才炸）。
- **Subagent prompt 必須明寫「branch check first」**：Task 3 有 subagent 開局在 main，差點留 stray file；Task 4+ 都明寫就沒事。
- **TDD 的 RED state 不可跳**：每個 Task subagent 先跑 pytest 確認 `AttributeError` 再 impl，這機械紀律讓「測試真的跑過」有硬證據，不是「我以為測試會紅」的自證。
- **rate limit 不影響工作流**：中途 `superpowers:code-reviewer` agent 撞 limit，inline 輕量 review 補位即可，不需改流程。

### 六、檔案異動

**新增**：
- `scripts/fetch_threads_post.py`（~180 行）
- `tests/test_fetch_threads_post.py`（37 tests）
- `tests/fixtures/relay_kanisleo_DXO2PlPEoOQ.json`（78KB）
- `docs/superpowers/plans/2026-04-24-fetch-threads-post.md`（~1200 行，Revision 1 含審查修正）

**修改**：
- `pyproject.toml`（新增 `[project.optional-dependencies].prototype = ["playwright>=1.40"]`）
- `.gitignore`（加 `.playwright-cli/`、`threads-*.png`）
- `docs/handoffs/session-handoff-20260424.md`（本區塊）

**未動**：
- 0423 handoff（不回改）
- C 路線所有檔案（`docs/dev/ak-threads-booster-research.md`、`skills/threads-angle-gate/`、roadmap）
- App Review 檔案
- 既有代碼（`threads_client.py`、`threads_cli/`、`threads_pipeline` 等）

**仍待清理（P2 持續）**：
- `threads-kanisleo-post.png`（已加 `.gitignore` glob 掩蓋，未實刪）
- `.playwright-cli/`（同上）

### 七、收工回寫

- [x] 12 commit 推上 `origin/feat/fetch-threads-post`（`01de228`..`295bede`）
- [x] PR #4 建立：https://github.com/azuma520/threads-pipeline/pull/4
- [x] Memory 更新：`project_progress_20260424.md` append「Session 13:15 — A 路線 prototype 完工」段落
- [x] `MEMORY.md` 索引：0424 條目已存在，無需新增
- [ ] **下次 session next action（linear）**：
  - **P0**. 決定 PR #4 下一步（等 review / 自 merge / 先不動）
  - **P1**（3 選 1）：
    - A 路線續攻：PR #4 merge 後晉升 `threads library fetch`（typer 整合、`images/` 下載、og:description fallback、更嚴謹 regression）
    - B 路線：錄 `profile_discovery.mp4` Plan B + Stage 5 送審
    - C 路線：實測 `threads-angle-gate` skill / 第 2 層 `planner.py` / merge `feat/advisor-plan`
  - **P2**. 清理 `threads-kanisleo-post.png` 與 `.playwright-cli/`（仍持續）
- [x] SSOT 清單更新：
  - **新增** A 路線 prototype 設計 + 執行紀錄：`docs/superpowers/plans/2026-04-24-fetch-threads-post.md`（晉升正式 CLI 時主控文檔切換）
  - 其餘 SSOT 不變

---

## Session 17:17

### 一、今日聚焦

- 清理 working tree 積壓（0422–0423 未 commit 的 profile_discovery + App Review docs），PR #4 功能實測

### 二、完成事項

- **Working tree 拆 3 批**：
  - Batch 1 → commit `d34b010` 上 `feat/fetch-threads-post`：3 份 handoff（0422/0423/0424）+ `docs/lessons/` 2 份 + `.gitignore` 加 `.reference/`
  - Batch 2 → 新 branch `feat/profile-discovery`（從 main 拉）2 commits 推 origin：`76ca758` feat(profile) + `e682c06` docs(app-review)
  - 垃圾 → `.reference/` 23MB PDF + page images 直接 gitignore，不 commit
  - `batch-a-lessons.md` 改動是 typo + formatter 噪音，revert 掉
- **PR #4 功能實測 6 項全綠**：
  - 單元測試 `tests/test_fetch_threads_post.py` 37/37
  - 全 repo `pytest` 229/229
  - Default run（A+B）：counts `{A:1,B:1,C:4,D:6,E:0}` = 12，kept 2（= 0424 13:15 anchor 精確命中）
  - `--include-replies`：kept 8（+D 6）
  - `--include-replies --include-self-replies`：kept 12（+C 4 +D 6）
  - Bad URL：stderr ERROR + exit 1
- **實戶實測**：抓 `@addisonaithinking/post/DXamvEgE1D2`（ChatGPT 生圖模板懶人包）
  - total 26 / counts `{A:1,B:6,C:0,D:19,E:0}`
  - 預設 kept 7 = A + 6 B（主文 + 5 模板 + 成果），作者觀點一次收齊
  - `--include-replies` kept 26：D 的 19 則讀者回覆全抓進來

### 三、洞見紀錄

- **「模板包型貼文」的典型讀者反應 = 100% save 行為**：addisonaithinking 那篇 19 則讀者回覆裡，17 則只是「留 / 留己看 / 存 / 筆記」，沒有任何 dialogue / 問題 / 辯論。演算法上拿到大量 save 但對話深度為零——這類內容擴散強、收藏強，但 community-building 效果有限。**對 advisor 的啟示**：如果目標是觸及 + 被收藏，複製這結構；如果目標是對話 + 信任，這格式不對。未來若要做 lesson 檔可引此例。
- **未 commit 積壓會越滾越大**：0422 handoff + 0423 profile_discovery 一整套（CLI + 34 tests + 8 份 app-review 文件）全卡在 working tree 快兩天沒動，切 feature branch 時差點被塞進錯的 PR scope。**規則**：session 尾聲檢查 `git status`，不屬於當前 branch 的變更立刻切 branch 或 stash 標註歸屬。

### 四、阻塞/卡點

- 無

### 五、行動複盤

- **分類 working tree 應該先做、再寫 commit**：今天先花時間把 3 批檔案用 diff 逐個分類（哪些是 batch 1 的 handoff、哪些是 batch 2 的 profile、哪些是純噪音），再動 commit。省掉「commit 完才發現塞錯分支」的災難。未來遇到「working tree 一團亂」情境，這模式可直接套用。
- **實戶實測可以一次 confirm 兩件事**：(1) 工具 functional OK，(2) 工具產出的素材真的有學習價值。原本只打算驗第 1 項，意外在實測中長出「模板包 = 100% save」的洞見，是免費 bonus。

### 六、檔案異動

**修改（batch 1 / 已 commit `d34b010`）**：
- `.gitignore`（加 `.reference/`）
- `docs/handoffs/session-handoff-20260423.md`（append 0423 18:07 Playwright 探索區塊，早餐 session 已寫）
- `docs/handoffs/session-handoff-20260424.md`（append 本 Session 17:17 區塊）

**新增（batch 1 / 已 commit `d34b010`）**：
- `docs/handoffs/session-handoff-20260422.md`（補 commit，原本 untracked）
- `docs/lessons/agent-first-tooling.md`、`docs/lessons/data-is-information.md`

**Batch 2 / `feat/profile-discovery` branch（已推 origin，未開 PR）**：
- `76ca758` feat(profile)：`threads_client.py` +168 / `threads_cli/profile.py` 新 / `threads_cli/cli.py` +2 / `skills/threads-cli/SKILL.md` +2 / `tests/test_threads_client.py` +17 / `tests/test_threads_client_profile.py` 新 / `tests/test_cli_profile.py` 新 / `scripts/probe_profile_discovery.py` 新
- `e682c06` docs(app-review)：`resubmission-plan.md` +121 + 6 份 demo script + `recording-checklist.md` + `submission-notes.md`

**本 session 新增的實戶實測素材**（drafts/ gitignored、本地保留）：
- `drafts/library/2026-04-24_addisonaithinking_DXamvEgE1D2/`（post.md 5.8KB + meta.json + relay.json + screenshot.png）

**Revert（噪音）**：
- `docs/dev/batch-a-lessons.md`（原本 working tree 的改動只有一個 typo + formatter 表格重排，checkout 回 HEAD）

### 七、收工回寫

- [x] Memory 更新：`project_progress_20260424.md` append「Session 17:17 — working tree 清理 + PR #4 功能實測 OK」段落
- [x] `MEMORY.md` 索引：0424 條目已存在，無需新增
- [x] **3 個 branch 狀態**：
  - `feat/fetch-threads-post`：11 commits ahead of main（10 A 路線 + 1 batch 1 handoff），PR #4 open
  - `feat/profile-discovery`：2 commits ahead of main，branch 推上 origin，**尚未建 PR**（等 B 路線討論後再決定）
  - `feat/advisor-plan`：原狀（C 路線等實測再動）
- [ ] **下次 session next action（linear）**：
  - **P0**. PR #4 決定：自 merge / 等 review / 先擱
  - **P1**. `feat/profile-discovery` branch 決定：開 PR / 保留 / 併進 B 路線送審動作
  - **P2**（3 選 1）：
    - A 路線續攻：PR #4 merge 後晉升正式 CLI（`threads fetch`、images 下載、og:description fallback、嚴謹 regression）
    - B 路線：錄 `profile_discovery.mp4` Plan B + Stage 5 送審
    - C 路線：實測 `threads-angle-gate` skill / 第 2 層 `planner.py` / merge `feat/advisor-plan`
  - **P3**. 清理 `threads-kanisleo-post.png` 與 `.playwright-cli/`（持續待辦）
- [x] SSOT 清單（本 session 不變）

---

## Session 17:18

### 一、今日聚焦

- 實測 `threads-angle-gate` skill（0824 接力棒 P0 / 本 session 主線）
- 順便把 skill 註冊進 `.claude/skills/` 讓 `Skill` 工具叫得到

### 二、完成事項

- **Skill 註冊**：`.claude/skills/threads-angle-gate/` 建立（`ln -s` 在 Windows Git Bash 降級為檔案複製，不是真 symlink；junction 方案試 `mklink /J` 前需 `rm -rf` 權限被擋，停在複製模式）
  - 結果：`Skill` 工具可以正常 invoke；available skills 清單熱載入看得到
  - 副作用：以後改 `skills/threads-angle-gate/SKILL.md` 不會自動同步到 `.claude/skills/`
- **`threads-cli` 漂移發現**：`skills/threads-cli/SKILL.md` 8948 bytes（今天 `M`）vs `.claude/skills/threads-cli/SKILL.md` 8047 bytes（0417 舊版）。使用者指示這是 CLI 開發中刻意狀態，**暫不處理**
- **跑一次完整 gate 流程**，使用者拋「作家的 PISA 日記法 + 我 harness 有類似機制」題目
  - 中途使用者貼出作家第二篇文章（Framework / SOP / Reflection 三資產），對齊「邊取」語意
  - 共創 pivot：**初始素材是「作家 PISA 日記法」→ 共創收斂到「AI 工具協作裡容易被忽略的一環：複盤機制」**
  - 三個共創關鍵詞全部由使用者自主講出：「我們」（刻意第一人稱）、「邊做、邊取、邊迭代」、「這些是大家會忽略的事情」
- **產出** `drafts/ai-tool-reflection-rhythm.angle.md`（source: co_created）
- **另一篇 candidate 記於 `related_future_post`**：「AI 是工具，也是團隊成員」（使用者自主 articulate：「我認為我跟 AI 是一個協作團隊」），defer 不入本篇

### 三、洞見紀錄

- **Skill 經得起 adversarial live run**：我中途提了個 edgy sharpness（「沒有反思節奏就只是在搭工具箱不是做系統」），使用者 reject 後我立即吸收並 re-draft 成 gentle 版本。Skill 鐵律「願意現場改變想法」運作正常——但這條鐵律**必須在 AI 自己已經有傾向時才會被測試到**，純 compliance 的訪談輪次測不出來。
- **Gate 的真正價值 = 防止 surface reading**：初始素材明面上看是「作家 PISA 日記法」，gate 走完才浮出「AI 工具協作裡被忽略的複盤機制」。如果直接寫，幾乎必然寫成「我也有類似做法分享」的扁平共鳴文——surface reading 的陷阱。
- **「我 vs 我們」是 gate 挖出的單句銳利點**：使用者自述「我認為我跟 AI 是一個協作團隊」——這是他過去沒明說、但一直在做的事被訪談挖出來 articulate 的時刻。Defer 成另一篇時機到了會是真的有份量的 post。
- **Windows Git Bash 的 `ln -s` 默認行為是複製不是 symlink**，不設 `MSYS=winsymlinks:nativestrict` 不會切到 native symlink。這種平台差異對 skill/plugin 分發是坑——寫安裝文件時不能假設 `ln -s` 有效。

### 四、阻塞/卡點

- **過程讚 / 成果未知**：使用者自己說的——gate 過程跑得順，但 angle.md 能不能真的變好貼文要等下一階段（填內文）才知道。gate 只負責定角度，驗不了結果。
- **Skill 註冊目前是複製模式**，維護要手動 sync（或下次改用 junction / 啟用 Developer Mode symlink）。

### 五、行動複盤

- **TDD for docs 的第三輪驗證**：早上 skill 寫完跑 2 輪 subagent RED-GREEN-REFACTOR，下午第三輪是**真使用者實測**。三輪都抓到需改進的點或確認規則有效——這模式持續值得。
- **Meta problem first / task second 的時機**：中途使用者問「skill invoke 什麼意思」+「我們做 skill 註冊」— 這類 meta 技術問題打斷訪談不是壞事，但要**明確跳出/跳回訪談者角色**讓使用者感受到切換。我在跳回時宣告「（skill 正式載入，進訪談者模式）」有效，無宣告會讓使用者混淆。
- **Source label 嚴格執行沒失敗**：兩次帶觀察進場（Turn 9「邊做邊學 vs 另外撥時間」、Turn 10「我們 vs 我」）都用明示 phrase「這是我個人的觀察」開頭——skill 的 phrase-level enforcement 在真實對話裡不難守，反而幫我避免 soft-assertion 的誘惑。

### 六、檔案異動

**新增**：
- `.claude/skills/threads-angle-gate/SKILL.md`（複製自 `skills/threads-angle-gate/SKILL.md`，含附帶 `.claude_review_state.json` 被一起複製過來）
- `drafts/ai-tool-reflection-rhythm.angle.md`（C 路線第 1 層首份真實產出）

**修改**：
- `docs/handoffs/session-handoff-20260424.md`（append 本 Session 17:18）

**未動**：
- `skills/threads-angle-gate/SKILL.md` 源檔（skill 規則不需改，三輪驗證都通過）
- `threads-cli` 漂移（使用者指示保留）
- 代碼（純 skill 測試，零代碼）
- A 路線 PR #4 / B 路線 `feat/profile-discovery` / C 路線其他檔案

### 七、收工回寫

- [x] Memory：`project_progress_20260424.md` 要 append「Session 17:18 — angle-gate skill 首次真實測試 + `drafts/ai-tool-reflection-rhythm.angle.md` 落檔」段落
- [x] `MEMORY.md` 索引：0424 條目已存在，無需新增
- [ ] **下次 session next action（linear）**：
  - **P0**. 決定 `drafts/ai-tool-reflection-rhythm.angle.md` 是否要繼續往下走（填內文 → Threads 貼文）。要的話下一階段可以把使用者累積的復盤紀錄拿進來當真實案例素材（sharpness 三個點舉例）
  - **P1**（跟 13:15 接力棒合併）：
    - PR #4 決定：自 merge / 等 review / 先擱
    - `feat/profile-discovery` branch：開 PR / 保留 / 併進 B 路線送審
    - A / B / C 三路線 3 選 1（同 17:17 接力棒）
  - **P2**. 若要正規化 skill 註冊（單一 source of truth 不漂移），研究 Windows Developer Mode 或 `mklink /J` junction（本 session 被 `rm -rf` 權限擋停）
  - **P3**. 清理 `threads-kanisleo-post.png` / `.playwright-cli/`（持續待辦）
- [x] SSOT 清單：
  - **新增** C 路線第 1 層首份真實 angle.md：`drafts/ai-tool-reflection-rhythm.angle.md`（後續填內文流程進場的輸入）
  - 其餘 SSOT 不變
