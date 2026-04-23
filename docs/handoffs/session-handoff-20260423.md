# Session Handoff — 2026-04-23

> 本檔為當日 append-only 工作紀錄。每個 session 結束時加一個 `## Session HH:MM` 區塊，**禁止修改前面 session 的內容**。

---

## Session 00:30

### 一、今日聚焦

- Meta App Review 第一輪結果到手（2026-04-22 寄達），處理重送策略

### 二、完成事項

**A. 結果摘要與拒絕原因分析**

- 2 個核准：`threads_basic`、`threads_manage_insights`
- 6 個拒絕：`content_publish` / `keyword_search` / `manage_replies` / `read_replies` / `manage_mentions` / `profile_discovery`
- 6 個拒絕理由完全一致（螢幕錄影不符合 use case end-to-end）
- 識別關鍵線索：Meta 模板末尾的 server-to-server 宣告條款，正是本 app 架構特性，上次未宣告導致審查員以一般 app 標準判斷

**B. 三項決策（2026-04-23）**

- Q1 範圍：A——一次全送
- Q2 profile_discovery：Y——排除（代碼無實際 use case，硬送違反產品邊界原則）
- Q3 追蹤方式：做成文檔管制，實際執行時才建 Task

**C. CLI 現況盤點（grep 驗證）**

| Permission | 現有 CLI | 缺口 |
|---|---|---|
| `content_publish` | `threads post publish` / `publish-chain` | 無 |
| `keyword_search` | `threads posts search` | 無 |
| `read_replies` | `threads post replies` | 無 |
| `manage_replies` | `threads reply`（只有新增） | **缺 hide/unhide** |
| `manage_mentions` | — | **整個功能缺** |

**D. 建立 App Review 主控文檔**

- 新增：`docs/app-review/resubmission-plan.md`
- 包含：背景、拒絕原因分析、Architecture Note 英文草稿、6 階段計畫、CLI 缺口表、變更歷史
- 定位：SSOT，每 session 進來先讀、結束更新

### 三、洞見紀錄

- **Meta 拒絕模板是樣板，關鍵訊息在最後一段**：所有 permission 拿到一樣的樣板文字，真正有情報量的是末尾「如果是 server-to-server 請註明」那句——這是 Meta 告訴你「要怎麼改寫 Notes」，但藏得很深，不仔細讀會錯過。下次處理 Meta 審查回饋，先讀模板末尾附註再讀指控內容。
- **「被拒 ≠ API 不能打」**：使用者第一個反應是「沒權限怎麼 demo」，這是可以理解的誤解。正確認知：App Review 是「Advanced Access 升級審查」，Development Mode / Standard Access 下 app owner 帳號仍可呼叫所有 API，只是範圍限自己。Demo 用自己帳號就夠，審查員看的是「app 怎麼用 API」不是「對多少外部用戶生效」。
- **profile_discovery 的識別流程**：grep 代碼 → 發現除了「取自己 profile」外完全無呼叫 → 判定為當初勾選但無實作。這是「產品邊界原則」memory 的實際應用——不為 demo 新增沒有真實需求的功能。

### 四、阻塞/卡點

- 5 份 demo 腳本尚未撰寫（Stage 2）
- `hide/unhide` 兩個 API 方法 + CLI 指令尚未實作（Stage 3）
- `mentions` API 方法 + CLI 指令尚未實作（Stage 3）
- 5 部 demo 影片尚未錄製（Stage 4）

### 五、行動複盤

- **用戶提出「沒權限怎麼 demo」時反應不夠快**：第一次回覆著重技術計畫，沒主動預判這個疑問。第二次用戶追問才釐清。教訓——提出「重錄 demo」計畫時，應該同步解釋「為什麼你能錄」，不要讓使用者自己湊出這個關鍵認知
- **建文檔前先盤點代碼是對的**：grep CLI 後才寫 gap table，一次到位不用回頭改。如果先寫文檔再盤點，gap 表格欄位會空著或猜錯
- **文檔結構決策**：`docs/app-review/` 獨立目錄、主控文檔當 SSOT、腳本分檔存——這是為了配合「階段執行」的工作節奏，避免單一大檔滾雪球

### 六、檔案異動

**新增**：
- `docs/app-review/`（新資料夾）
- `docs/app-review/resubmission-plan.md`（主控文檔，~170 行）
- `docs/handoffs/session-handoff-20260423.md`（本檔）

**未動**：
- 所有代碼（`threads_client.py` / `threads_cli/*` 本次未修改）
- `memory/` 所有檔案（本次未更新；下階段 Stage 6 時再批次更新）

### 七、收工回寫

- [x] 建立 `memory/project_progress_20260423.md`
- [x] 更新 `memory/MEMORY.md` 索引
- [x] 更新 `memory/project_advanced_access.md`（審查結果 + 重送範圍）
- [x] 更新 `memory/project_api_access_constraint.md`（現況：僅 insights + basic 核准）
- [ ] **下次開工 next action**：從主控文檔 Stage 2 或 Stage 3 開工，三選一：
  - **(1) 先寫 5 份 demo 腳本**（純文字工作，不碰代碼）
  - **(2) 先補 CLI 兩塊缺口**（代碼工作：hide/unhide + mentions）
  - **(3) 並行**：同時寫 3 個 CLI 已齊的 permission 腳本 + Agent 補 CLI 缺口
- [ ] 主控文檔：`docs/app-review/resubmission-plan.md`（session 開工第一件事讀這份）

---

## Session 02:00

### 一、今日聚焦

- App Review 重送計畫 Stage 3（CLI 補齊）——執行並收尾

### 二、完成事項

**A. 主控計畫文檔**
- `docs/superpowers/plans/2026-04-23-cli-app-review-gaps.md` 建立（writing-plans skill 產出的 8-task 實施計畫）

**B. Subagent-Driven 執行 7 個 task**
- Task 1 ✅ `hide_reply` API helper（`threads_client.py` + 3 unit tests）— commit `04b6154`
- Task 2 ✅ `list_mentions` API helper（`threads_client.py` + 4 unit tests）— commit `25eb0c4`
- Task 3 ✅ `threads reply` 轉為 Typer sub-app（add/hide/unhide）— commit `fd68004`
- Task 4 ✅ reply hide/unhide CLI 測試（6 tests）— commit `d95f206`
- Task 6 ✅ `threads account mentions` 子命令 + 6 tests — commit `1436b5d`
- Task 7 ✅ docs 同步（CLAUDE.md / resubmission-plan / skills/threads-cli/SKILL.md）— commit `4bd8c5f`
- Task 8 ✅ 本 handoff + 驗證（full suite 192 passed、--help smoke 通過）

**C. 指標**
- Full suite: 192 passed（原 180 + 12 新測試）
- feat branch: `feat/app-review-cli-gaps`，6 commits
- 計畫階段覆蓋：Stage 3 ✅ 已完成（resubmission-plan.md 已更新）

**D. CLI 新增面向**
- `threads reply add <post_id> <text>` ← 原 `threads reply`（breaking rename）
- `threads reply hide <reply_id>`（新）
- `threads reply unhide <reply_id>`（新）
- `threads account mentions [--limit N] [--cursor C] [--json]`（新）

**E. 驗證輸出（Task 8 現場收集）**

`threads reply --help` Commands section：
```
add      Reply to an existing post.
hide     Hide a reply on your post.
unhide   Unhide a previously-hidden reply.
```

`threads account mentions --help` Options section：
```
--limit    INTEGER  Max mentions (1-100) [default: 25]
--cursor   TEXT     Pagination cursor
--json              Output as JSON envelope
```

### 三、洞見紀錄

- **Subagent 遇到 plan 裡的 test spec bug 會自己修，這是對的**：Task 4 的 plan 裡寫了 `CliRunner(mix_stderr=False)`，但 repo 已經升級 Typer 不吃這個參數；subagent 沒 BLOCKED 回報，而是直接套既有 repo 的 `CliRunner()` pattern 把測試寫完。這屬於「機械性修補，不改變測試意圖」，判斷得好。Plan 的精度有天花板，中低層級的 API 變動 subagent 應該自行消化。
- **Plan 覆蓋不全的同步遷移，subagent 主動補齊**：Task 3 只說搬 `test_threads_cli.py`，但 `tests/test_cli_blackbox.py` 也有對 `threads reply` 的 3 個黑箱測試，subagent 看到 full suite 掉 3 個會壞就順手遷了。這是「看到明顯對等變更沒做，補上」的合理自主權，不是越權。
- **Code review 的 Important 若定位為 polish，不該擋 task**：Task 7 收到 code-quality reviewer 給的兩點 Important（test 缺 HTTPError-without-response / `mentions_cmd` 沒跟 `replies_cmd` 用同一個 error mapper），User 決定 approve + 記 follow-up 而不是重跑 task。這個判斷對的：兩點都不是正確性 bug，是一致性/完整性瑕疵，塞進下次 polish batch 比硬擋收尾合理。

### 四、阻塞/卡點

- Stage 2 demo 腳本尚未寫（5 份）
- Stage 4 影片錄製未啟動
- Stage 5 送審尚未進行

Follow-up（從 code review 收到的 polish items，下次可順手做）：
- `test_cli_reply_manage.py` 缺 HTTPError-without-response 與 missing-token 測試
- `mentions_cmd` 錯誤碼對應應跟 `replies_cmd` 一致用 `_map_request_error`（目前只回 `API_ERROR`）

### 五、行動複盤

- **`writing-plans` → `subagent-driven-development` 組合在 7-task 規模上效益高**：每個 subagent 任務邊界清楚（1 helper + N tests / 1 CLI 改動 / 1 doc 更新），不需要跨 task context。plan 寫精準，subagent 幾乎沒問題問，commit cadence 也乾淨。下次類似規模可直接複用這個流程。
- **Plan 的盲區通常在「測試 spec 的隱藏假設」**：主要邏輯 plan 都寫對，但 CliRunner 版本、fixture shape、既有 pattern 這類隱藏假設 plan 往往沒交代。下次寫 plan 可考慮在 Test Plan 章節加一行「參考 `tests/<existing>.py` 的 pattern 寫新測試」，把默認對齊明示化。
- **Code review 的 Critical vs Important 要預先分級**：reviewer 給 Important 時，User 要當場決定「擋 task」還是「follow-up」。今天兩筆都歸 follow-up、寫進 handoff「阻塞/卡點」，節奏沒被打斷。下次遇到 Important 先問「這是正確性 bug 還是一致性瑕疵？」正確性 bug 擋，瑕疵排。

### 六、檔案異動

**新增**：
- `docs/superpowers/plans/2026-04-23-cli-app-review-gaps.md`（實施計畫）
- `tests/test_threads_client_manage.py`（3 tests）
- `tests/test_threads_client_mentions.py`(4 tests）
- `tests/test_cli_reply_manage.py`（6 tests）
- `tests/test_cli_account_mentions.py`（6 tests）

**修改**：
- `threads_client.py`（+`hide_reply`、+`list_mentions`、+`_DEFAULT_MENTION_FIELDS`）
- `threads_cli/reply.py`（完整改寫，單命令 → Typer sub-app）
- `threads_cli/cli.py`（reply 註冊方式）
- `threads_cli/account.py`（+`mentions_cmd`、imports）
- `tests/test_threads_cli.py`（reply tests 遷移）
- `tests/test_cli_blackbox.py`（reply blackbox tests 遷移）
- `CLAUDE.md`（reply CLI 範例）
- `skills/threads-cli/SKILL.md`（reply syntax 同步）
- `docs/app-review/resubmission-plan.md`（Stage 3 標記完成）

**未改（刻意保留）**：
- `publisher.py` / `main.py` / `insights_tracker.py` / `analyzer.py` / `advisor.py` / `report.py`——核心 pipeline 完全未動
- `feat/advisor-plan` branch 狀態維持

### 七、收工回寫

- [x] `memory/project_progress_20260423.md` 已在 00:30 session 建立，Stage 3 進度另補在此 handoff 七、
- [x] `memory/MEMORY.md` 索引保持最新（Stage 3 完成不另增 memory entry，因為進度同步在進度 memory 內）
- [x] `docs/app-review/resubmission-plan.md` Stage 3 標記 ✅ 已完成
- [ ] **下次開工 next action**：二選一
  - **A. 進 Stage 2**：寫 5 份 demo 腳本（`docs/app-review/demo-script-{permission}.md`），純文字工作
  - **B. 先 merge feat branch 到 main**：6 個 commit 已集中、spec + quality review 都過，可乾淨 merge；之後再進 Stage 2
- [ ] 開工先讀：`docs/app-review/resubmission-plan.md`（SSOT）+ 本 handoff 最新 Session 區塊

---

## Session 14:19

### 一、今日聚焦

- App Review 重送計畫 Stage 2（demo 腳本）——一次寫完 5 份

### 二、完成事項

**A. State 釐清**
- 發現 Stage 3 的 6 個 commits 已在 `local main`（非 feat branch），`feat/app-review-cli-gaps` 已不存在；另存在 `publish/app-review-cli-gaps`（與 `origin/publish/app-review-cli-gaps` 同步，未 merge 進 origin/main）
- `origin/main` 尚未包含 Stage 3，local 與 remote diff 共 13 檔 / 675 行（未 push）

**B. Stage 2 五份 demo 腳本全部完成**
- `docs/app-review/demo-script-content-publish.md`
- `docs/app-review/demo-script-keyword-search.md`
- `docs/app-review/demo-script-read-replies.md`
- `docs/app-review/demo-script-manage-replies.md`
- `docs/app-review/demo-script-manage-mentions.md`

每份一致含 5 章節：Use case / Demo 步驟表 / 旁白逐句 / 螢幕字幕對照 / 事前準備。每支目標 ≤ 2 min、英文 UI + 英文旁白，跟 Stage 4 錄影規範對齊。

**C. API 現況盤點（read-only CLI 診斷）**
- `threads posts list` ✅ 通，owner 有 25 則歷史貼文（最新 2026-04-02）
- `threads post replies 17952165552108332` ✅ 通，最新貼文已有 **10 則真實他人 reply**（足夠 `read_replies` 與 `manage_replies` demo 用，不需協調第二帳號）
- `threads account mentions` ❌ HTTP 500。curl 直打抓到 body：`{"error": {"message": "Tried accessing nonexisting field (threads_mentions)", "code": 100, "type": "THApiException"}}`——此 endpoint 在 `manage_mentions` 核准前完全鎖住

**D. 範圍縮減決策：5 → 4**
- 排除 `manage_mentions`，本輪重送從 5 個縮到 4 個
- 理由：endpoint locked 前無法錄 live demo，硬送重蹈「demo 不完整」覆轍
- `manage_mentions` 延到下一輪單送，採 Architecture-Demo 策略（CLI 實作 + 原始碼 + Meta docs + Threads UI）取代 live API demo
- 4 個本輪清單：`content_publish` / `keyword_search` / `manage_replies` / `read_replies`

**E. 計畫文檔同步**
- `resubmission-plan.md`：
  - Stage 2 checkbox ✅（4 個「本輪用」+ 1 個 ⏸️「延後單送」）
  - 1.3 節重送清單更新為 4 個 + 延後單送清單
  - Stage 4 checklist 5 部 → 4 部（mentions 劃掉註解）
  - Stage 5 分「本輪 4 個」與「次輪單送 mentions」
  - 變更歷史 +2 行（Stage 2 完成 / API 診斷 + 範圍縮減）
- `demo-script-manage-mentions.md`：頂端加 Deferred 警示；Plan A 保留為 live demo 版；新增 Plan B 作 Architecture-Demo 腳本（7 幕組合 + pre-recording setup + 送審 Notes 文案樣板）
- `memory/project_api_access_constraint.md`：補記 `/me/threads_mentions` endpoint-locked 診斷結果

### 三、洞見紀錄

- **CLI 簽章掃描是腳本精準度的先決條件**：在寫腳本前先 parallel 讀 `post.py` / `posts.py` / `reply.py` / `account.py`，把 dry-run 行為、`--confirm --yes` 語義、JSON envelope 欄位都抓到，腳本的「期望輸出」和「旁白」才能寫得精準到 reviewer 可照抄驗證。下次 Meta 要再送任何 permission，先從 CLI 掃描起步，不要從 template 套話。
- **`keyword_search` demo 用英文關鍵字是刻意選擇**：Standard Access 下中文會觸發 `EMPTY_RESULT_CJK` warning（我們已經內部驗證），對 reviewer 是噪音。demo 的目的是展示 happy path，不是展示邊界行為。把這個理由寫進事前準備第 4 段，未來再送審不會誤踩。
- **腳本假設可能脫離現實，寫完一定要用 read-only CLI 驗過一遍**：原本規劃「協調第二帳號做 3 則 reply / 2 則 mention」——實測發現 owner 帳號最新貼文就已經有 **10 則真實他人 reply**，完全不需要外部協調。相反地，`manage_mentions` 的 endpoint 則是**完全鎖住**（curl body: `Tried accessing nonexisting field`），原本計畫的「Mentions tab 協調 2 則 @mention」做了也沒用。先驗再規劃 vs 先規劃再驗，差了一整輪協調成本。下次 demo 規劃進 Stage 4 前強制先 read-only 盤點。
- **Permission-locked endpoint 是 Meta Graph API 的經典悖論**：要核准才能呼叫 → 要呼叫才能 demo → 要 demo 才能核准。唯一出路是 Architecture-Demo（CLI 原始碼 + Meta docs + Threads UI 組合影片）加明確的 pre-approval disclosure。與其跟這個悖論硬拼，務實做法是先過能過的，把 app 信任度建起來再單送難 permission。

### 四、阻塞/卡點

- `publish/app-review-cli-gaps` branch 的推送/merge 策略待定（origin/main 尚未包含 Stage 3 commits）——User 需要決定是「push main」還是「走 PR 流程」還是「維持 publish 分支備份不動」
- Stage 4（影片錄製）待啟動——**現狀無外部協調阻塞**（既有 10 則 reply 已足）；只差拍攝本人執行
- Stage 5 送審尚未進行（本輪 4 個）
- `manage_mentions` 本輪排除，延後單送——需等 4 個核准後再走 Architecture-Demo
- Follow-up（從 Stage 3 code review 留下）：`test_cli_reply_manage.py` 缺 HTTPError-without-response / missing-token 測試；`mentions_cmd` 錯誤碼要對齊 `replies_cmd` 的 `_map_request_error` — 可排進下次 polish batch

### 五、行動複盤

- **State 釐清放在最前面是對的**：session 開頭 `git log` 與 `git branch -a` 一跑就發現 handoff 寫的 branch 狀態已過期。如果沒先核對就照 handoff 寫「先 merge feat branch」會做錯事。下次進 session，讀完 handoff 的同時一定要跑 `git status` / `git branch -a` / `git log --oneline -10` 交叉驗證。
- **腳本一次寫 5 份用相同模版是快的**：每份都用「5 章節」結構，差異只在 command set 與事前準備。這種「格式統一、內容各異」的批次文件工作很適合「單 session 內一次到位」，不需要拆成 5 個 task。但每份的事前準備章節必須針對該 permission 調整，不能複製貼上。
- **TaskCreate 規模控制**：這次 8 個 task 對 5 份腳本 + 文檔更新稍偏多。更精簡可以做：1 個掃 CLI task + 1 個「寫完 5 份腳本」task + 1 個收尾 task = 3 個。下次類似規模用 3 個 task 夠了。

### 六、檔案異動

**新增**：
- `docs/app-review/demo-script-content-publish.md`
- `docs/app-review/demo-script-keyword-search.md`
- `docs/app-review/demo-script-read-replies.md`
- `docs/app-review/demo-script-manage-replies.md`
- `docs/app-review/demo-script-manage-mentions.md`（含 Plan A + Plan B）

**修改**：
- `docs/app-review/resubmission-plan.md`（Stage 2 ✅、1.3 重送清單 5→4、Stage 4/5 拆本輪與次輪、變更歷史 +2 行）
- `docs/handoffs/session-handoff-20260423.md`（本 Session 區塊 append + 範圍縮減追記）
- `memory/project_api_access_constraint.md`（補記 `/me/threads_mentions` endpoint-locked）

**未動**：
- 所有代碼（threads_client / threads_cli / tests 本 session 完全未動）
- 任何 branch / commit（純 docs 工作）

### 七、收工回寫

- [x] `memory/project_progress_20260423.md` — 既有檔案，本 session 僅 docs 推進，另在下面 next action 提示補充
- [x] `memory/MEMORY.md` 索引保持最新（Stage 2 完成不增新 entry；進度在 progress memory）
- [x] `docs/app-review/resubmission-plan.md` Stage 2 標 ✅
- [ ] **下次開工 next action**（線性序）：
  - **S1. Stage 4 錄影**（本輪 4 部）：content_publish / keyword_search / read_replies / manage_replies。現狀無外部協調阻塞——最新貼文已有 10 則真實 reply 可用。本人拍攝；Agent 可協助產錄影前置 checklist（把腳本 `<POST_ID>` / `<REPLY_ID>` 換成實值）。manage_replies 拍完記得 unhide 還原。
  - **S2. Stage 5 送審**：4 個 permission Notes 定稿 + 4 部影片上傳 + submit。
  - **S3. 等審 + 收尾**：預期 5-10 工作天。
  - **S4. 次輪單送 manage_mentions**：4 個核准後啟動；先實測 `/me/threads_mentions` 是否仍 locked；未解鎖走 Plan B（Architecture-Demo，腳本在 `demo-script-manage-mentions.md` Plan B 段）。
  - （平行，非阻塞）Stage 3 commits 推送策略決定、Stage 3 code review polish items。
- [ ] 開工先讀：`docs/app-review/resubmission-plan.md`（SSOT）+ 本 handoff 最新 Session 區塊

---

## Session 17:03

### 一、今日聚焦

- C 路線（AI 生草稿工作流）4 層完整設計定稿——對照研究文件從「AK 點到點吸收」擴展到「整體架構對話式設計」

### 二、完成事項

**A. C 路線 4 層全部設計定稿**

| 層 | 結論 |
|---|---|
| 第 1 層 選角度 Gate | **v6 定稿**——訪談者 + 共創者，AI 永遠用問句出場（發問 / 總結+詢問），共鳴 = 問答迴路收斂到使用者點頭 |
| 第 2 層 planner 升級 | 讀整份 angle.md；Stage 1 挑框架吃 topic + sharpness；Stage 2 生骨架強引導不強制每則扣回 |
| 第 3 層 填內文輔助 | 最薄一層，兩個小幫手（顯示骨架 metadata + 手動撈歷史段落），不碰創作核心 |
| 第 4 層 AI 防味 | AK 借核心通用項 + 客製 cosplay 堆疊檢測（符號密度 / 機械斷行 / voice-patterns 過度命中）+ 整合 advisor review 第 7 維度，軟提醒不擋 |

**B. 核心設計句（使用者原話，寫進文件）**

- 「切入點只是一個主軸跟方向，沒有主旨，但是要表達的東西就是在表達的過程，能夠圍繞它展開及表達，這樣就夠了」— 第 2 層基調
- 「AK 那套可以參考，但是不一定要非得應用」— 第 4 層基調
- 「從後面需要什麼，去思考這一段需要什麼」— 第 2 層設計哲學
- 「人寫，工具不碰創作核心」— 第 3 層基調

**C. 文件擴展並 commit**

- `docs/dev/ak-threads-booster-research.md`：從 untracked 狀態擴展到 **701 行並 commit 進 git（`f825db8`）**
- 新增章節：v1→v6 演進表、4 層設計定稿、仍待決清單、與其他層接點說明

**D. Skill 願景討論**

- 目標、願景、使用者幫助、使用場景（6 個）、trade-off 已討論完畢
- 下個 session 實作 SKILL.md 時可直接寫入「About / Vision / When to use」章節

### 三、洞見紀錄

- **v6 的「AI 永遠用問句出場」是一招解雙玄**：把「AI 主導 vs 使用者主導」的張力跟「共鳴怎麼操作化」的玄學一次解掉。判斷包成問句 → 主導權自動回使用者；共鳴 = 問答迴路收斂到使用者點頭，不再是 AI 內感。
- **4-14 翻車的根因是「沒有切入點」，不是「沒有強制規則」**：之前以為「強制每則扣回切入點」可對治流水帳。實際這是重複犯「把框架當必撒清單」的錯。正確解法是第 1 層把根因解了，第 2 層強引導 + 軟提醒即可。設計防呆機制本身也可能變成 cosplay 式清單化，要警惕。
- **「從後面需要往前推」**：第 2 層該吃什麼欄位，不是看第 1 層產出什麼，而是看第 3 層 + 最終產出需要什麼反推。這讓 angle.md 保留所有欄位（包括對話原話），不因「第 2 層用不到」就刪。
- **設計迭代 v1→v6 的失敗模式相似**：每次都是「把解失敗的方法做成硬規則」。v1 5 題固定 + 強制對比句；v4 學習教練機制；連第 2 層都差點再犯（強制每則扣回切入點，被使用者 pushback 才校正）。

### 四、阻塞/卡點

- 無

### 五、行動複盤

- **犯過兩次「用太多 jargon 導致使用者不懂」**：Q1/Q3 第 2 層介接問題、Q1-Q4 第 3 層全組問題。使用者明確說「什麼意思不是很董」才修正。教訓：對使用者討論設計時，**第一輪就要用白話**——使用者是「不寫 code、不打 CLI、透過 Agent 開發」，`stage` / `sharpness` / `source_quotes` 這類英文術語對他陌生
- **使用者 pushback「為什麼你一定要強制」時立刻承認被說服並給新設計**：這個即時校正比嘗試捍衛立場好。對他是好的
- **「建議怎麼做」類問題，順序推薦（先 X 再 Y）比選項清單（A/B/C）有效**：推薦需要理由支撐；但選項清單在使用者要對比時才有價值
- **逐次迭代（v1→v6）比一次給完美設計好**：使用者喜歡參與設計收斂的過程，不喜歡被餵終版

### 六、檔案異動

**新增（並 commit）**：
- `docs/dev/ak-threads-booster-research.md`（701 行；commit `f825db8`）

**未動**：
- 所有代碼
- `feat/advisor-plan` branch（依決策 B：等 C 路線全部落地再 merge）
- App Review 相關檔案（本 session 未觸碰）

### 七、收工回寫

- [x] 更新 `memory/project_progress_20260423.md`（補 C 路線設計完成段）
- [x] 更新 `memory/project_ak_threads_booster_compare.md`（反映 4 層定稿狀態）
- [x] 更新 `memory/MEMORY.md` 索引兩條相關 one-liner
- [ ] **下次 session next action**：寫 `threads-angle-gate` skill 草案（C 路線第 1 層落地；最有原創性、不依賴其他層；參考 `docs/dev/ak-threads-booster-research.md` 第 1 層定稿章節 + 本 session 的 skill 願景討論內容）
- [ ] 平行可做：候選點 #1（Semantic Freshness Gate）PoC——誤群風險驗證
- [ ] 主控文檔（SSOT）：
  - C 路線設計：`docs/dev/ak-threads-booster-research.md`
  - App Review：`docs/app-review/resubmission-plan.md`（Session 14:19 留下的待辦，仍未處理）
