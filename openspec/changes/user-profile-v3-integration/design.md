## Context

`threads-write-flow` v3 是 dump-first 9-step 寫貼文 pipeline（0507 merge 到 main、a1f1cc8）、v3.0.1 已 patch 6 條（0511）。

5/8 acceptance test 出現 5 輪 reframe：第 1 輪「主線重抓」（Step 2 抓事件列表不是個人觀察）、第 4 輪「鉤子 reframe」（agent 預設「感激 AI」角色）。

5/9 user 自己寫 SEO 月報：開頭「一年前剛接觸行銷的我」、user 主動下角色設定、整篇順、上 Threads 沒大改。

對比結論：v3 缺一層「**用戶角色設定資料**」── 不是 user voice（文字風格）、是「文章中的我是誰」這個可塑造角色 + user 跨多篇共通的內核 / 紅線 / 表達偏好。

0511 下午到 0512 早上跨日 explore：3-layer 模型（內核固定 / 角色設定 per-piece / 文風 derive）+ 從 user 10 篇 Threads surface 4 種角色樣子 + 9 內核 + 8 紅線、4 個 thread 全 settle。design notes 寫進 `docs/dev/2026-05-11-user-profile-v3-integration-design.md`。

`02-user-profile.md` + `02-user-profile.template.md` 0512 commit 落地（2819921）、gitignore 規則同步加上。

## Goals / Non-Goals

**Goals:**

1. Layer 1 載入機制 codify ── Step 1 entry 讀 `02-user-profile.md` internalize 為 baseline
2. Step 2 主線抓取重定義 ── 從事件列表改為「角色設定（4 維）+ 個人經驗 + 個人觀察 / 心得」
3. Step 2.5 訪談 trigger 明確化 ── 4 條 trigger（觀察 / 動機 / 判斷 / 4 維 cover 缺漏）
4. Step 3 角色偏移診斷 ── vs 8 紅線 + vs 4 樣子
5. SKILL.md setup section ── 給未來 user 從 template copy + fill 的指引
6. 不破壞既有行為 ── 9 step 框架 / 訪談 + 刪除法 / show 不 tell / 反模板化全保留

**Non-Goals:**

- 不改 00-philosophy.md / 01-user-expression.md（既有 reference 已穩定）
- 不改 Step 4 / 5 / 6 / 7 / 8 / 9 行為（design notes Section 3.5 / 3.6 標 P2、本 change 不做）
- 不做 drift 自動監控（先落地測試、實測再調 reread 範圍）
- 不改 memory（既有 `feedback_interview_alignment.md` / `project_content_philosophy.md` audience 不同、不衝突）
- 不改 threads_pipeline 本體（pipeline / CLI / analyzer 全部與本 change 無關）

## Decisions

### D1：載入機制 ── Step 1 全載 + 關鍵 step 按需 reread

選 design notes 方案 F（vs 方案 D 每 step 全載、方案 E 完全 lazy）。

| Step | reread section | 為什麼 |
|------|---------------|--------|
| Step 2 主線 | Section 7（4 維 + 樣子）+ Section 4（內核） | 抓角色設定 + anchor 內核 |
| Step 3 診斷 | Section 5（8 紅線）+ Section 7（樣子對照） | 偏移診斷需要對照 |
| Step 5 鉤子 | Section 5（紅線）+ Section 4（內核） | 鉤子 Fit Check |
| Step 8 反模板 | Section 5 + 6（紅線 + 表達偏好） | 抓 generic / 翻譯腔 |

**Step 1 entry 行為**：
- ✅ 用 Read 工具讀 `references/02-user-profile.md` 全部、internalize
- ❌ 「我讀了你的 9 條內核、現在開始 dump」（機械感）
- ✅ 直接進 dump、agent 內部已載入

**Alternatives Considered（design notes Section 3.1）**：
- 每 step 全載 → context bloat、模型注意力分散
- 完全 lazy → Step 1 沒 base、agent 預設 generic（5/8 痛點來源）

### D2：Step 2 主線重定義

主線 = 3 件事：

1. **這篇的角色設定（4 維）**：身份 / 視角 / 思維 / 背景 ── surface 後 user verify
2. **個人經驗（事件層）**：發生什麼 / 場景 / 對話 / 細節 / 行動 ── 從 dump 直接抓
3. **個人觀察 / 心得 / 判斷（重量層）** ← 5/8 痛點所在：user 從這經驗中看到什麼 / 為什麼這樣做 / 怎麼判斷下一步 / 學到什麼 ── 從 dump 抓、沒有則 Step 2.5 補

方法：每件事用「surface + 給選項 + user 刪除法」、不是純開放問。

對位 4 種角色樣子（profile.md Section 7）：抓完 4 維後、surface「這篇看起來像樣子 A？還是 B？或別的組合？」── user 用刪除法選或修。

### D3：Step 2.5 訪談 trigger 明確化

4 條 trigger：

- dump 沒講「我從中看到 X」 → 問「你從這經驗中看到什麼 / 學到什麼」
- dump 沒講「我為什麼這樣做」 → 問「你那當下為什麼選 X 不選 Y」
- dump 沒講「我怎麼判斷」 → 問「下一步你怎麼決定」
- 角色 4 維沒 cover → surface 假設讓 user 確認

保留「沒有就沒有」原則：問了真沒有就接受、不勉強補。

形式：
- ✅ 諮詢式：「我聽下來你那當下的觀察可能是 X、是這樣嗎？」
- ❌ 評估式：「你 dump 缺觀察、要補」

### D4：Step 3 角色偏移診斷

新增診斷項（疊在既有優缺診斷上）：

- 是不是踩了 8 條紅線之一？哪一條？
- 是不是把角色預設成 generic（譬如「AI 受惠者」）？
- 是不是文風跟內核衝突？

用 4 種角色樣子當參考：
- 確認這篇角色設定屬於 A / B / C / D 哪個或哪個組合
- 如果四個都不像 → 可能是新樣子、surface 給 user 確認、**不擅自寫進 profile**

### D5：iter 規則 ── 先落地測試再調 reread 範圍

不在 spec 一次寫死。spec 列當前 reread 對照表（D1 表格）、但留註記「實測 drift 情況後可調」。

理由：sense > 機械原則 ── 寫死全部 reread 範圍會在實測前就鎖死、違反訪談 + 刪除法迭代邏輯。

## Risks / Trade-offs

| 風險 | Mitigation |
|------|-----------|
| **載入太多 → context bloat** | profile.md 簡短 codify、不寫長 spec；agent 寫到 Step 7 不再 reread |
| **角色設定機械化** | 用訪談 + 刪除法、不用問卷；surface 假設讓 user 刪、不要求 user 填 |
| **過度 enforcement** | 違反 sense > 機械、ceiling 沒拉但 floor 拉重；用「訊號」not「判死」 |
| **profile.md 跟現實脫節** | user 主動 review 才更新；agent 不自動寫 |
| **8 紅線 / 4 樣子變死規定** | 樣子是參考、不是 enum；user 寫新樣子要允許 |
| **新 user 沒 02-user-profile.md skill 跑掛** | SKILL.md setup section + Step 1 entry 檢測檔案不存在時提示「請先從 template 建立」 |

## Migration Plan

無破壞性變更：

1. 既有 user（azuma520）：`02-user-profile.md` 已 0512 落地、跑新 spec 直接生效
2. 新 user：走 SKILL.md setup section、copy template + fill
3. SKILL.md 改動 backward-compatible ── Step 1-3 行為強化、不取消任何既有 step

回滾：revert SKILL.md 改動即可（02-user-profile.md / template 不需移除、未被 SKILL.md 引用時等同 dormant）。

## Open Questions

1. **載入機制細節**：Read 工具還是 `@reference` 引用？傾向 Read（跟 00-philosophy / 01-user-expression 同模式）── apply 時確定
2. **drift 監控閾值**：怎麼判斷 Step 5 / 8 是否 drift？目前先按 D1 對照表跑、實測後可能要調
3. **template 跟實際 profile 同步策略**：實際 profile 更新時要不要同步 sanitize 回 template？目前手動、看頻率高再 codify
