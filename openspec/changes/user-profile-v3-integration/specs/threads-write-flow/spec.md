## ADDED Requirements

### Requirement: User Profile Layer 1 Reference

`threads-write-flow` skill MUST 在 Step 1 entry 載入 `references/02-user-profile.md` 作為用戶身份背景 + 寫作核心的固定層 baseline。

載入後 agent SHALL internalize 為基底（包含工作 / 身份 / 主要受眾 / 長期方向 / 內核 N 條 / N 條紅線 / 表達方式偏好 / 角色 4 維 schema + N 樣子實例 / 草稿品質下限）、不在對話中展開、不機械列出「我讀了 X 規則」。

若 `references/02-user-profile.md` 不存在、skill SHALL 提示 user 從 `references/02-user-profile.template.md` copy 並 fill、不繼續 Step 1。

#### Scenario: profile 存在、Step 1 順利進入 dump

- **WHEN** user 啟動 `threads-write-flow` skill 進入 Step 1、`references/02-user-profile.md` 已存在
- **THEN** skill 內部讀取整份 profile internalize、直接邀請 user dump、不顯示「我讀了 X 條內核」這類機械訊息

#### Scenario: profile 不存在、skill 提示 setup

- **WHEN** user 啟動 skill 進入 Step 1、`references/02-user-profile.md` 不存在
- **THEN** skill 提示 user 從 `references/02-user-profile.template.md` copy 一份成 `02-user-profile.md`、fill 完再回來；不繼續 Step 1

---

### Requirement: User Profile Per-Step Reread

`threads-write-flow` skill SHALL 在 Step 2 / Step 3 / Step 5 / Step 8 entry 按需 reread `references/02-user-profile.md` 的相關 section、避免長 pipeline drift。

對照表：

| Step | reread section | 目的 |
|------|---------------|-----|
| Step 2 主線 | Section 7（4 維 + 樣子）+ Section 4（內核） | 抓角色設定 + anchor 內核 |
| Step 3 診斷 | Section 5（N 條紅線）+ Section 7（樣子對照） | 偏移診斷 |
| Step 5 鉤子 | Section 5（紅線）+ Section 4（內核） | 鉤子 Fit Check |
| Step 8 反模板 | Section 5（紅線）+ Section 6（表達偏好） | 抓 generic / 翻譯腔 |

reread 後 agent MUST 內部使用、不在對話中展開列出 section 內容（避免機械感）。

iteration 規則：本對照表為 v3.1 初版、實測 drift 情況後可調 reread 範圍。

#### Scenario: Step 2 reread Section 7 + Section 4

- **WHEN** skill 從 Step 1 進入 Step 2 主線抓取
- **THEN** skill 內部讀取 profile Section 7（4 維 schema + N 樣子）+ Section 4（內核），用於後續主線抓取邏輯

#### Scenario: Step 3 reread Section 5 + Section 7

- **WHEN** skill 從 Step 2 / 2.5 進入 Step 3 診斷
- **THEN** skill 內部讀取 profile Section 5（紅線）+ Section 7（樣子），用於角色偏移診斷

#### Scenario: Step 5 reread Section 5 + Section 4

- **WHEN** skill 從 Step 4 進入 Step 5 鉤子挖掘
- **THEN** skill 內部讀取 profile Section 5（紅線）+ Section 4（內核），用於 Hook Fit Check

#### Scenario: Step 8 reread Section 5 + Section 6

- **WHEN** skill 從 Step 7 進入 Step 8 反模板化
- **THEN** skill 內部讀取 profile Section 5（紅線）+ Section 6（表達偏好），用於 generic / 翻譯腔診斷

---

### Requirement: Step 2 Main Thread Redefinition

`threads-write-flow` Step 2「主線抓取」MUST 抓三件事，不是純事件列表：

1. **這篇的角色設定（4 維）**：身份（這篇的我是誰）/ 視角（怎麼看這件事）/ 思維（思考方式）/ 背景（context）── surface 後 user verify
2. **個人經驗（事件層）**：發生什麼 / 場景 / 對話 / 細節 / 行動 / 選擇 ── 從 dump 直接抓
3. **個人觀察 / 心得 / 判斷（重量層）**：user 從這經驗中看到什麼 / 為什麼這樣做 / 怎麼判斷下一步 / 學到什麼 ── 從 dump 抓、沒有則 Step 2.5 補

方法 SHALL 用「surface 假設 + 給選項 + user 刪除法」、不用純開放問。

抓完 4 維後 skill SHALL 對位 profile Section 7 樣子實例、surface「這篇看起來像樣子 A / B / C / D / 混合 / 新樣子？」、由 user 用刪除法 verify 或修；如四個樣子都不像、surface 給 user 確認新樣子、**不擅自寫進 profile**。

#### Scenario: Step 2 抓 4 維 + surface 對位樣子

- **WHEN** Step 2 開始、agent 完成 dump reread
- **THEN** agent surface「這篇的我是誰 / 怎麼看 / 怎麼思考 / 在什麼 context」4 維假設給 user 用刪除法 verify；4 維 settle 後 surface「像樣子 A / B / C / D / 混合？」給 user 選

#### Scenario: dump 缺重量層 trigger 進 Step 2.5

- **WHEN** Step 2 抓完事件層、但 dump 沒含 user 觀察 / 心得 / 判斷
- **THEN** agent 進 Step 2.5 諮詢式訪談補料、不直接寫進 Step 3

#### Scenario: 4 樣子都不像、surface 新樣子

- **WHEN** agent 抓完 4 維、對位 profile Section 7 四個樣子都不像
- **THEN** agent surface「這像新樣子、你怎麼描述？」給 user 確認、不擅自寫進 profile.md

---

### Requirement: Step 2.5 Consultative Interview Triggers

`threads-write-flow` Step 2.5「諮詢式訪談」MUST 用 4 條明確 trigger 啟動補料、不純靠開放式問題：

- dump 沒「我從中看到 X」 → 問「你從這經驗中看到什麼 / 學到什麼」
- dump 沒「我為什麼這樣做」 → 問「你那當下為什麼選 X 不選 Y」
- dump 沒「我怎麼判斷」 → 問「下一步你怎麼決定」
- 4 維（身份 / 視角 / 思維 / 背景）有 cover 缺漏 → surface 假設讓 user 用刪除法 verify

訪談形式 SHALL 用諮詢式、不用評估式：

- ✅ 「我聽下來你那當下的觀察可能是 X、是這樣嗎？」
- ❌ 「你 dump 缺觀察、要補」

「沒有就沒有」原則 MUST 保留：問了真沒有、agent 接受、不勉強補。

#### Scenario: dump 沒觀察、trigger 問觀察

- **WHEN** Step 2.5 進入、Step 2 抓的事件層沒對應 user 觀察 / 心得
- **THEN** agent 用諮詢式問「你從這經驗中看到什麼」、user 若答「沒有」agent 接受不勉強

#### Scenario: 4 維缺背景、surface 假設

- **WHEN** Step 2.5 進入、Step 2 抓的 4 維「背景」沒 cover
- **THEN** agent 用「我猜這篇 context 可能是 X、對嗎？」surface 假設給 user 刪除法 verify

#### Scenario: user 說沒有、不勉強補

- **WHEN** agent 問完 trigger、user 回「沒有」或刪掉 agent 假設
- **THEN** agent 接受、進下一個 trigger 或結束 Step 2.5、不重複追問

---

### Requirement: Step 3 Character Drift Diagnosis

`threads-write-flow` Step 3「優缺診疼」MUST 加角色偏移診斷項（疊在既有優缺診斷上）：

- 是不是踩了 profile Section 5 的 N 條紅線之一？哪一條？
- 是不是把角色預設成 generic（譬如「AI 受惠者」/「工具感激型」）？
- 是不是文風跟 profile Section 4 內核衝突？
- 這篇角色設定對位 profile Section 7 哪個樣子（或混合 / 新樣子）？

任何偏移診斷 surface 給 user、user 用刪除法決定要不要回 Step 2 / 2.5 重抓 ── skill 不擅自重啟前面 step。

#### Scenario: 偵測踩紅線、surface 給 user

- **WHEN** Step 3 進入、agent 內部判定 Step 2 抓的角色設定踩 Section 5 某條紅線（譬如「AI 受惠者」）
- **THEN** agent surface「目前角色像 AI 受惠者、會踩紅線 #1、建議回 Step 2 重抓、要嗎？」由 user 決定

#### Scenario: 角色對位樣子確認

- **WHEN** Step 3 進入、Step 2 已 settle 4 維
- **THEN** agent surface「這篇角色像樣子 A 還是 B、或哪個混合？」給 user 用刪除法 verify

#### Scenario: 文風 vs 內核衝突 surface

- **WHEN** Step 3 進入、agent 內部判定既有寫稿方向跟 Section 4 內核衝突（譬如「教師口吻」vs 內核「誠懇不裝」）
- **THEN** agent surface「目前風格偏教師口吻、跟內核 #3 衝突、要怎麼調？」由 user 決定

---

### Requirement: SKILL.md Setup Section

`skills/threads-write-flow/SKILL.md` MUST 含 setup section、告訴未來 user 怎麼從 `references/02-user-profile.template.md` 建立自己的 `references/02-user-profile.md`。

setup section SHALL 包含：

- 為什麼需要 Layer 1 用戶角色設定資料（一句說明：避免 agent 預設 generic 角色）
- copy 命令 / 路徑
- fill 指引（指向 template 內 placeholder）
- 註記：實際 `02-user-profile.md` 已 gitignored、不會推上 GitHub

#### Scenario: SKILL.md 含 setup section

- **WHEN** reviewer 讀 `skills/threads-write-flow/SKILL.md`
- **THEN** 找到 setup section、說明 02-user-profile.md 從 template copy + fill 的流程
