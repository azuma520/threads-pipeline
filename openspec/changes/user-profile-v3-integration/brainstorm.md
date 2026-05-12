## Design Summary

把「**用戶角色設定資料**」這層 codify 成 Layer 1 reference（`02-user-profile.md`）、整合進 `threads-write-flow` v3 的 Step 1 / 2 / 2.5 / 3，補 v3 缺的「先訂角色」這一層。

對應 0512 跨日 explore 跟 user 走過 3-layer 模型 + 4 樣子 + 9 內核 + 8 紅線、4 個 thread 全 settle、design notes 已寫進 `docs/dev/2026-05-11-user-profile-v3-integration-design.md`。

## Alternatives Considered

### 方案 A：揭露程度 ── 全揭露

- **做法**：02-user-profile.md 直接寫實際內容、commit 上 GitHub
- **優點**：透明、其他 user 容易看出 reference 怎麼填、不需要 setup 步驟
- **缺點**：個人資訊（軍人 20 年、鉦旺樂、家庭 context）leak 到 public repo；threads_pipeline 已 push GitHub、不可逆
- **為何未採用**：跨越「分享自己 vs 推銷自己」的邊界、不該強制其他 user 揭露這些資訊

### 方案 B：揭露程度 ── 全隱

- **做法**：02-user-profile.md 永遠 gitignore、不留範本
- **優點**：完全保護個人資訊
- **缺點**：其他 user 用這個 skill 時不知道 reference 該寫什麼結構、需要重新摸索
- **為何未採用**：違反 skill = floor 的原則、floor 之一就是「告訴 user 該怎麼設定」

### 方案 C：揭露程度 ── template + gitignore（採用）

- **做法**：實際 `02-user-profile.md` gitignore、公開 `02-user-profile.template.md` 含 placeholder、SKILL.md 寫 setup 步驟
- **優點**：保護個人資訊 + 給其他 user 結構參照；fail-safe（沒 setup 時 skill 知道要提示）
- **缺點**：多一個 setup 步驟、新 user 第一次用時要 copy + fill
- **為何採用**：兼顧隱私 + 可分享性、唯一無致命缺點的選項

### 方案 D：載入時機 ── 每 step 全載

- **做法**：每 step entry 都 Read 整份 02-user-profile.md
- **優點**：永遠不會 drift
- **缺點**：context bloat、9 個 step 重複載入造成模型注意力分散
- **為何未採用**：違反 sense > 機械、不必要的 reload

### 方案 E：載入時機 ── 完全 lazy

- **做法**：只在「明顯需要 anchor 內核」的 step 才載入
- **優點**：節省 context
- **缺點**：Step 1 dump 前沒 base、agent 預設 generic（譬如「AI 受惠者」）── 5/8 痛點來源
- **為何未採用**：解不掉 5/8 vs 5/9 對比的根本差異

### 方案 F：載入時機 ── Step 1 全載 + 關鍵 step 按需 reread（採用）

- **做法**：Step 1 entry Read 全部 internalize；Step 2 / 3 / 5 / 8 按需 reread 相關 section（4 維、紅線、表達偏好）
- **優點**：解 5/8 痛點（baseline 已 anchor）+ 避免 drift（關鍵 step 重新對齊）+ 不 over-load
- **缺點**：需要 codify「哪些 step reread 哪些 section」mapping
- **為何採用**：對應 5/8 痛點 + 訪談 + 刪除法判斷 + design notes Section 3.1 已細寫對照表

### 方案 G：profile 結構 ── 4 維 = 4 樣子

- **做法**：直接列 4 個樣子（A/B/C/D）、不抽 schema
- **優點**：直觀、好讀
- **缺點**：樣子變成 enum、user 寫新題材 surface 新樣子時 agent 不知道怎麼處理
- **為何未採用**：違反「樣子是參考、不是 enum」原則

### 方案 H：profile 結構 ── 4 維 schema + N 樣子實例（採用）

- **做法**：Section 7.1 寫 4 維 schema（身份/視角/思維/背景）、Section 7.2 寫 4 個實例樣子當參照
- **優點**：schema 處理「任何角色」、實例樣子當對照表；新樣子 surface 時可以擴充
- **缺點**：要寫得讓 agent 抓對「schema vs instance」關係
- **為何採用**：對齊 Thread B 跟 user 走完的結論、Section 7 已重寫為條列格式（agent 更好讀）

## Agreed Approach

採 C（template + gitignore）+ F（Step 1 全載 + 按需 reread）+ H（4 維 schema + N 樣子實例）的組合。

對應 4 個 thread settle：
- Thread A 揭露程度 → 方案 C
- Thread B 4 維 vs 4 樣子 → 方案 H
- Thread C 載入時機 → 方案 F
- Thread E memory 重複度 → 兩邊保留 + cross-reference（不在本 change scope、已 settle 0512）

### 為什麼這組勝出

5/8 acceptance（5 輪 reframe）vs 5/9 SEO 月報（直接順發）── 同 user、同題材、相隔 1 天、結果截然不同。差別是 5/9 user **自己**內建了 Layer 1 + 主動下 Layer 2 角色設定、5/8 agent 沒 Layer 1 + Layer 2 也沒抓到。

這組合解的就是「讓 agent 在 Step 1 拿到 Layer 1、Step 2 抓 Layer 2、Step 3 用 Layer 1 + Layer 2 做偏移診斷」── 把 5/9 的順移植到 agent 身上。

## Key Decisions

1. **Layer 1（內核）載入機制**：Step 1 entry 用 Read 工具讀 `references/02-user-profile.md`、internalize、不展開、不顯示「我讀了 X 條規則」（避免機械感）
2. **Step 2 主線重定義**：主線 = 角色設定（4 維）+ 個人經驗（事件層）+ 個人觀察 / 心得 / 判斷（重量層）、不是事件列表
3. **Step 2.5 訪談 trigger 明確化**：4 條 trigger（觀察 / 動機 / 判斷 / 4 維 cover）、保留「沒有就沒有」原則
4. **Step 3 角色偏移診斷**：vs 8 紅線 + vs 4 樣子；對「四個都不像」surface 給 user 確認新樣子
5. **iter 規則**：先用此策略落地 / 測試、看 drift 實際情況再調整 reread 範圍 ── 不是一開始就把所有 step 都 reread

## Open Questions

- **載入機制細節**：實作時是 Read 工具還是 `@reference` 引用？決定後再寫進 spec（傾向 Read 工具 ── 跟既有 `00-philosophy.md` / `01-user-expression.md` 同模式）
- **drift 監控**：怎麼判斷 Step 5 / 8 是否 drift？目前先按 design notes Section 3.1 對照表跑、實測後可能要再調
- **template 跟實際 profile 同步**：實際 profile 更新時要不要同步 sanitize 回 template？目前先手動、看頻率高再 codify
