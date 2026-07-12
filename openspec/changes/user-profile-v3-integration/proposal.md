## Why

v3 `threads-write-flow` skill 在 5/8 acceptance test 出現 5 輪 reframe（含 agent 預設「感激 AI」角色、主線抓事件列表非個人觀察）；5/9 SEO 月報同 user 同題材直接順發、差別是 user 主動下了「一年前剛接觸行銷的我」這個角色設定。對比結論：v3 缺一層「**用戶角色設定資料**」── agent 沒拿到固定身份背景 + 角色設定就被丟去寫稿、會預設 generic。現在處理是因為 0512 跨日 explore 已把 3-layer 模型 + 4 樣子 + 9 內核 + 8 紅線收齊、design notes 就緒、4 個 thread 全 settle。預期收益：把 5/9 的順移植到 agent 上、減少 reframe 輪數、抬高草稿品質下限。

## What Changes

**Step 1 dump entry**
- From: 直接進 dump、不載入用戶 profile reference
- To: Entry 用 Read 工具讀 `references/02-user-profile.md` internalize、不顯示「我讀了 X 規則」、進 dump
- Reason: 解 5/8 痛點（agent 預設 generic 角色）
- Impact: non-breaking、Step 1 行為微調

**Step 2 主線抓取**
- From: 主線 = 從 dump 抓事件 + 主軸
- To: 主線 = 角色設定（身份/視角/思維/背景 4 維）+ 個人經驗（事件層）+ 個人觀察 / 心得 / 判斷（重量層）三件事；reread Section 7 + Section 4
- Reason: 5/8 第 1 輪 reframe「主線重抓」根因
- Impact: non-breaking、Step 2 spec 重定義

**Step 2.5 諮詢式訪談**
- From: 沒講就主動問、開放式
- To: 4 條明確 trigger（觀察 / 動機 / 判斷 / 4 維 cover 缺漏）、保留「沒有就沒有」
- Reason: 訪談原則 + 刪除法 N=10+ 已成熟、純開放式對 user 反而難
- Impact: non-breaking、Step 2.5 spec 精細化

**Step 3 優缺診斷**
- From: 通用優缺診斷
- To: 加角色偏移診斷（vs 8 紅線 + vs 4 樣子）；reread Section 5 + Section 7
- Reason: 預防 Step 4 後再發現角色錯（5/8 第 4 輪「鉤子 reframe」根因）
- Impact: non-breaking、Step 3 spec 加診斷項

**新 reference 檔案**
- 新增：`skills/threads-write-flow/references/02-user-profile.md`（gitignored、實際個人版）
- 新增：`skills/threads-write-flow/references/02-user-profile.template.md`（公開範本）
- Reason: Layer 1 codify、template/實際分離保護個人資訊
- Impact: 已就緒（0512 commit 2819921）

**SKILL.md setup 步驟**
- 加段落：未來 user 怎麼從 template.md copy + fill 出自己的 02-user-profile.md
- Reason: skill = floor 之一 ── 告訴 user 怎麼設定
- Impact: SKILL.md 加 setup section

## Capabilities

### New Capabilities

- `threads-write-flow`: Dump-first 9-step 寫貼文 pipeline、含 Layer 1 用戶角色設定資料載入、Step 2 主線含 4 維角色設定、Step 2.5 諮詢式訪談、Step 3 角色偏移診斷

### Modified Capabilities

（無 ── 既有 `openspec/specs/` 是空的、threads-write-flow 是首次進 OpenSpec spec）

## Impact

- **檔案異動**：`skills/threads-write-flow/SKILL.md`（加 Step 1 entry 載入、Step 2 重定義主線、Step 2.5 trigger、Step 3 偏移診斷、setup section）
- **既有 reference**：`skills/threads-write-flow/references/00-philosophy.md`、`01-user-expression.md` 不動
- **新 reference**：`02-user-profile.md`（已 0512 落地、gitignored）+ `02-user-profile.template.md`（已 0512 落地、公開）
- **gitignore**：`skills/threads-write-flow/references/02-user-profile.md`（已 0512 落地）
- **docs**：`docs/dev/2026-05-11-user-profile-v3-integration-design.md` 不動（設計筆記、本 change 後仍有參考價值）
- **memory**：跟既有 `feedback_interview_alignment.md` / `project_content_philosophy.md` 不衝突 ── audience 不同（memory 跨專案、profile 寫作 specific）、無需 cross-reference 改動
- **breaking**：none ── 既有 user（azuma520）已有 02-user-profile.md、其他 user 走 setup section
