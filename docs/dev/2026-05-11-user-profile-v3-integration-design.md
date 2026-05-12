# user-profile 整合進 v3 threads-write-flow — 設計筆記

> 2026-05-11 explore 階段 — 不寫 code、不改 skill、只捕捉設計思考。
> 對應檔案：`skills/threads-write-flow/references/02-user-profile.md`（Layer 1 已 codify、放 skill references 內、按需載入）。
> 對應 5/8 acceptance test 痛點 + 5/9 SEO 月報順的對比洞察。
> 落地實作走 OpenSpec propose → design → tasks → apply 流程（**還沒做**）。

---

## 1. 問題定義

### 1.1 5/8 acceptance test 痛點
- 第 1 輪「主線重抓」── Step 2 抓的是事件列表、不是「user 的觀察 / 心得」
- 第 4 輪「鉤子 reframe」── agent 預設「感激 AI」、角色錯
- final 採 Codex line-edit + user 微調 ── Claude 主控寫稿不行

### 1.2 5/9 SEO 月報順
- user 自己寫、開頭主動下「一年前剛接觸的我」── 角色一鎖死、整篇順
- 「優化做完不是結束、要驗證」── 觀察直接 surface 在文章中

### 1.3 5/8 vs 5/9 對比結論
v3 缺一層：**先把 Layer 1（內核）載入、再把 Layer 2（per-piece 角色 + 觀察）抓對**。

5/9 順是因為 user **自己**內建了 Layer 1（他自己當然知道）+ 主動下 Layer 2 設定。
5/8 痛是因為 agent **沒有** Layer 1 載入、Layer 2 也沒抓對。

---

## 2. v3 既有 step 對照

| Step | 既有功能 | 要動嗎 | 動什麼 |
|------|---------|--------|-------|
| `00-philosophy` | 上位 5 原則 | 不動 | 已 codify show 不 tell / 訪談+刪除法 / sense>機械 / 沒有就沒有 |
| Step 1 dump | user 自由 dump | **加** | 載入 `references/02-user-profile.md` 當基底 |
| Step 2 主線 | 從 dump 抓主線 | **重定義** | 主線 = 角色設定 + 經驗 + 觀察 + 心得（不是事件列表）|
| Step 2.5 訪談 | 諮詢式補料 | **加 trigger** | 觀察 / 心得 / 角色 4 維沒抓到時主動問 |
| Step 3 診斷 | 優缺診斷 | **加** | 角色偏移診斷（vs 8 紅線 + vs 4 角色樣子）|
| Step 4 敘事 | 敘事草稿 | **加** | 角色設定一致性檢查 |
| Step 5 鉤子 | 鉤子挖掘 | **加** | Hook 須對齊角色設定 + 內核 |
| Step 6 校準 | user 介入 | 不動 | 已 OK |
| Step 7 修文 | 字句層 | 不動 | 已 OK |
| Step 8 反模板 | 機械訊號 + sense | 不動 | 已 OK |
| Step 9 串文 | 敘事邏輯先分段後 | 不動 | v3.0.1 已 patch |

---

## 3. 新增動作（按 step 細部）

### 3.1 載入策略：Step 1 全載 + 關鍵 step 按需 reread

**Step 1 entry 全載**：
- 讀取 `references/02-user-profile.md` 全部
- internalize 為基底、不展開、不顯示「我讀了 X 條規則」（避免機械感）

**後續關鍵 step 按需 reread 相關 section**（avoid drift）：

| Step | reread section | 為什麼 |
|------|---------------|--------|
| Step 2 主線 | Section 7（4 維 + 樣子）+ Section 4（內核）| 抓角色設定 + anchor 內核 |
| Step 3 診斷 | Section 5（8 紅線）+ Section 7（樣子對照） | 偏移診斷需要對照 |
| Step 5 鉤子 | Section 5（紅線）+ Section 4（內核） | 鉤子 Fit Check |
| Step 8 反模板 | Section 5 + 6（紅線 + 表達偏好） | 抓 generic / 翻譯腔 |

**為什麼這樣設計**：
- agent 沒 Layer 1、會預設 generic（譬如「AI 感激者」）── Step 1 全載解決
- 寫到 Step 5 / 8 時可能 drift、忘記 8 紅線 ── 關鍵 step reread 解決
- 但不每步全部 reread（context bloat）── 只讀相關 section

**反例 / 避免**：
- ❌ 「我讀了你的 profile、現在開始 dump」── 機械感
- ✅ 直接進 dump、agent 內部已載入

**迭代規則**：先用此策略落地 / 測試、看 drift 實際情況再調整 reread 範圍。

### 3.2 Step 2 主線抓取：重定義

**新主線 = 3 件事**：

```
1. 這篇的角色設定（4 維）
   ├─ 身份：這篇的我是誰
   ├─ 視角：怎麼看這件事
   ├─ 思維：思考方式
   └─ 背景：context
   ↓ surface 後 user verify

2. 個人經驗（事件層）
   ├─ 發生什麼
   ├─ 場景 / 對話 / 細節
   └─ 行動 / 選擇
   ↓ 從 dump 直接抓

3. 個人觀察 / 心得 / 判斷（重量層）← 5/8 痛點所在
   ├─ user 從這經驗中看到什麼
   ├─ 為什麼這樣做
   ├─ 怎麼判斷下一步
   └─ 學到什麼
   ↓ 從 dump 抓、沒有則 Step 2.5 補
```

**方法**：每件事用「surface + 給選項 + user 刪除法」、不是純開放問。

**對位 4 種角色樣子**（profile.md Section 7）：
- 抓完 4 維後、surface「這篇看起來像樣子 A？還是 B？或別的組合？」── user 用刪除法選或修

### 3.3 Step 2.5 訪談 trigger 明確化

**trigger 規則**：
- dump 沒講「我從中看到 X」 → 問「你從這經驗中看到什麼 / 學到什麼」
- dump 沒講「我為什麼這樣做」 → 問「你那當下為什麼選 X 不選 Y」
- dump 沒講「我怎麼判斷」 → 問「下一步你怎麼決定」
- 角色 4 維沒 cover → surface 假設讓 user 確認

**保留「沒有就沒有」原則**：問了真沒有就接受、不勉強補。

**反例 / 避免**：
- ❌ 評估式：「你 dump 缺觀察、要補」
- ✅ 諮詢式：「我聽下來你那當下的觀察可能是 X、是這樣嗎？」

### 3.4 Step 3 角色偏移診斷

**診斷項**：
- 是不是踩了 8 條紅線之一？哪一條？
- 是不是把角色預設成 generic（譬如「AI 受惠者」）？
- 是不是文風跟內核衝突？

**用 4 種角色樣子當參考**：
- 確認這篇角色設定屬於 A / B / C / D 哪個或哪個組合
- 如果四個都不像 → 可能是新樣子、surface 給 user 確認

### 3.5 Step 4 敘事草稿：角色一致性檢查

寫每段時 anchor 回去：
- 這段是 **這角色** 怎麼判斷？
- 這段是 **這角色** 怎麼觀察？
- 這段是 **這角色** 的語氣？

不一致 → flag、不直接斷死、surface 給 user。

### 3.6 Step 5 鉤子：對齊角色 + 內核

**Hook Fit Check**：
- 鉤子對應的「我」是不是這篇的角色設定？
- 鉤子是否引向 8 條紅線之一（譬如「再不學 AI 就完了」= 販賣焦慮）？
- 鉤子是不是從文章內核反推、不是吸睛後再寫文？

---

## 4. 落地優先序

### P0（必做、最小可行）
1. 建 `references/02-user-profile.md`（已建、放 skill references 內）
2. Step 1 entry 載入 profile
3. Step 2 重定義「主線」= 角色 + 經驗 + 觀察 + 心得

### P1（強化）
4. Step 2.5 訪談 trigger 明確化（3 條觀察 trigger + 4 維 trigger）
5. Step 3 角色偏移診斷（vs 8 紅線 + vs 4 樣子）

### P2（後續）
6. Step 4 角色一致性檢查
7. Step 5 Hook Fit Check

---

## 5. 風險 / 注意

| 風險 | 防範 |
|------|------|
| **載入太多 → context bloat** | profile.md 簡短 codify、不寫長 spec；agent 寫到 Step 7 也不再 reread |
| **角色設定機械化** | 用訪談+刪除法、不用問卷；surface 假設讓 user 刪、不要求 user 填 |
| **過度 enforcement** | 違反 sense > 機械、ceiling 沒拉但 floor 拉重；用「訊號」not「判死」 |
| **profile.md 跟現實脫節** | user 主動 review 才更新；agent 不自動寫 |
| **8 紅線 / 4 樣子變死規定** | 樣子是參考、不是 enum；user 寫新樣子要允許 |

---

## 6. 接下來（不是現在做）

1. **user verify profile.md 沒漏** — 9 條內核 + 8 條紅線 + 4 樣子 + 受眾 + 方向、全部都對
2. **載入機制**（已決定）：
   - skill 在 Step 1 用 Read 工具直接讀 `references/02-user-profile.md`
   - 跟既有 `00-philosophy.md` / `01-user-expression.md` 同模式（v3 conditional loading）
3. **走 OpenSpec propose → design → tasks → apply 流程**：
   - propose：v3.1 patch — user-profile + Step 1/2/2.5/3 整合
   - design：scenarios / requirements 細寫
   - tasks：每個 step 改動的 TODO 列表
   - apply：實作

---

## 7. 相關文件 / context

- `skills/threads-write-flow/references/02-user-profile.md` — Layer 1 實際內容（**已 gitignore、個人資訊不公開**）
- `skills/threads-write-flow/references/02-user-profile.template.md` — 公開範本（用戶 copy 後 fill 成 02-user-profile.md）
- `skills/threads-write-flow/SKILL.md` — v3 主檔
- `skills/threads-write-flow/references/00-philosophy.md` — v3 上位 5 原則
- `skills/threads-write-flow/references/step-02-main-thread.md` — 待改
- `skills/threads-write-flow/references/step-02.5-interview.md` — 待改
- `docs/handoffs/session-handoff-20260508.md` — 5/8 acceptance test 痛點來源
- `.archive/tmp-claude-step7-article-20260508.md` — 5/8 final draft（對比樣本）
- 5/9 published post：`https://www.threads.com/@azuma01130626/post/DYHs6eXAadJ` — 5/9 對比樣本
- 既有 memory：`project_content_philosophy.md`（信任優先）、`feedback_interview_alignment.md`（訪談+刪除法）
