# Step 03：原文優點與弱點診斷

**前置哲學**：本 step 遵守 references/00-philosophy.md 的 5 條原則。

## Step 3 Entry：reread profile Section 5 + Section 7

進入 Step 3 第一件事 ── reread `references/02-user-profile.md` 的 Section 5（N 條紅線）+ Section 7（4 維 + 樣子實例）。

**為什麼 reread**：Step 3 要做兩種診斷 ── (1) 既有的優缺診斷（對照 4.1 / 4.2）、(2) 新加的角色偏移診斷（vs 紅線 + vs 樣子）。reread 確保紅線清單跟樣子對照表 fresh。

**reread 後行為**：內部使用、不在對話中展開列出。

## 目標

在動結構之前，先看清楚原始素材的優點（要保留）跟弱點（要動）+ 確認角色設定沒偏移。

## AI 在乎什麼

辨認 user 的真實感、具體事件、原話對話、情緒張力、認知轉折、個人語氣 ── 這些是文章的靈魂、不能被改掉。同時辨認背景過載 / 主線不清 / 核心太晚 / 句子太長 / 補充語干擾 / 語氣太說教 / 開頭太平 / 結尾太空泛 ── 這些是要動的弱點。

## 為什麼

很多 AI 的修文會把 user 的真實感一起改掉、變成標準 AI 文。先做「優點 vs 弱點」診斷可以讓 AI 修文時知道哪些不能碰。

## 怎麼跑

AI 對照 references/01-user-expression.md（4.1 / 4.2 兩節清單），從素材中找出：

- 哪幾句是優點（標明保留原文 / 保留語氣、引用 quote + 對應 4.1.X）
- 哪幾段是弱點（標明該動的方向、引用段落 + 對應 4.2.X）

**輕量訪談介入**（呼應訪談原則 + spec subagent validation 問題 1.3）：

標完之後 surface 給 user：「**我聽下來這幾句是你的特色（quote + 4.1.X）、這幾段是要動的（quote + 4.2.X）── 有沒有抓反的？**」── 給 user 一個輕量介入點，避免 Step 3 抓錯一路歪到 Step 7 才發現。

**跟 Step 2.5 的分工**：Step 3 看的是「user 表達習慣」（語氣 / 密度 / 補充語 / 哪句該保留）── 不再追問新素材。Step 2.5 已經補完素材缺口；Step 3 只診斷已有素材的優缺、不問新東西。除非發現 Step 2.5 漏掉「會讓文章無法成立的關鍵缺口」── 才回 Step 2.5 補料。

## 角色偏移診斷（v3.1 新增）

疊在既有優缺診斷上、跑 3 項判斷：

| # | 診斷項 | 怎麼判斷 |
|---|---|---|
| 1 | **踩紅線** | Step 2 抓的角色設定（譬如「AI 受惠者」）vs profile Section 5 N 條紅線 ── 命中任何一條 surface |
| 2 | **預設 generic** | 角色像 generic 模板（「感激 AI 者」/ 「初學者敘述」這類）而非 user 個人 voice ── surface |
| 3 | **文風 vs 內核衝突** | 既有寫稿方向（譬如「教師口吻」）跟 profile Section 4 內核（譬如「誠懇不裝」）衝突 ── surface |

**對位樣子確認**：Step 2 抓的 4 維、對位 profile Section 7 樣子（A / B / C / D / 混合 / 新樣子）── 在 Step 3 再 surface 一次給 user 確認、避免 Step 2 settle 後到 Step 4-7 才發現對錯。

**任何偏移 surface 給 user、user 用刪除法決定要不要回 Step 2 / 2.5 重抓**：

> 「**目前角色像 AI 受惠者、會踩紅線 #1 + 不像你 profile Section 7 任何一個樣子。建議回 Step 2 重抓角色 4 維。要嗎？**」

**邊界**：AI 不擅自重啟前面 step、surface 後 user 決定。「沒有就沒有」原則：實際沒偏移就不勉強找。

## sense 層

- 哪句算「真實材料」哪句算「補充語干擾」── 模型 sense
- 弱點處理力道（砍多少 / 拆多細） ── 模型 sense

## Gate（進 Step 4 前必過）

- [ ] **Step 3 entry reread 過 profile Section 5 + Section 7**（fresh read in this message）
- [ ] 對照 4.1 / 4.2 都跑完（每條至少 sense 過一遍）
- [ ] **角色偏移診斷 3 項都跑完**（紅線 / generic / 文風衝突）── 命中項 surface 給 user
- [ ] **對位樣子確認**：Step 2 抓的 4 維對位 Section 7 樣子、surface 給 user 用刪除法 verify
- [ ] 輕量訪談 surface 給 user、user 確認沒抓反
- [ ] 不追問新素材（除非發現 Step 2.5 漏的關鍵缺口、明確說明後回 Step 2.5）
