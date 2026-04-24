# Agent-first 工具鏈設計：五個原則

**日期**：2026-04-15
**脈絡**：討論「CLI 對 App 開發的幫助（角度 B）」時整理出來的系統設計原則。

背景定位：**工具的主要使用者是 AI Agent，不是人類**。設計目標是「幫 Agent 工作更順、犯錯更少」。這個定位業界稱為 **Agent-native tooling** 或 **LLM-first design**。

---

## Agent 在工具鏈上會遇到的痛點

| Agent 痛點 | 典型情境 |
|---|---|
| 記不住專案的慣用指令 | 每次查 `PYTHONUTF8=1 python -m threads_pipeline.main` 對不對 |
| 不確定現在狀態 | Token 過期了嗎？資料庫有東西嗎？上次跑到哪？ |
| 誤觸有副作用的操作 | 不小心真發文、不小心刪掉資料 |
| 驗證繞圈 | 改完一個東西，不知道該跑哪個測試確認 |
| 錯誤訊息看不懂 | API 回 `{"error":{"code":190}}`，Agent 要 Google 才知道是 Token 問題 |
| 文件散落 | 要找「怎麼跑 advisor」可能在 README、CLAUDE.md、docs/ 三個地方 |

---

## 五個設計原則

### 原則 1：常用操作封裝成「一個短指令」

不是為了省字，是為了**降低 Agent 犯錯的面積**。

```
Before: PYTHONUTF8=1 python -m threads_pipeline.main
After:  threads-pipeline run
```

**品味判斷**：哪些指令該被封裝？**會重複 3 次以上、或有固定前綴/後綴的**。

---

### 原則 2：提供狀態查詢指令

Agent 不能「憑感覺」，要能查到客觀事實。

範例：
- `threads token status` → 還剩幾天過期
- `threads db stats` → 追蹤了幾個貼文、最後更新時間
- `threads-advisor history` → 最近分析過哪些草稿

**品味判斷**：Agent 在做決策前需要哪些事實？把那些事實做成查詢指令。

---

### 原則 3：危險操作 dry-run 優先 + 明確確認

`threads post publish` 預設 dry-run、要 `--confirm --yes` 才真發，這就是教科書等級的 Agent-first 設計。

**品味判斷**：哪些操作「做錯會痛」？
- 花錢
- 公開（發文、寄信、送通知）
- 不可逆（刪除、覆寫）
- 通知別人

以上操作都該**雙門檻**（dry-run 預設 + 明確確認旗標）。

---

### 原則 4：錯誤訊息包含「下一步建議」

Agent 不會「靈機一動」，需要錯誤訊息明確指路。

```
❌ "Error: 401 Unauthorized"
✅ "Token 已過期（2026-04-10）。執行 threads token refresh 續期，
   或到 .env 更新 THREADS_ACCESS_TOKEN。"
```

**品味判斷**：如果 Agent 看到這個錯，它能不能自己修？不能的話，補什麼資訊它就能修？

---

### 原則 5：文件即介面（Agent-readable docs）

Agent 讀的是 `--help` 輸出、`CLAUDE.md`、`README.md`。這些是 Agent 的「UI」。

檢驗標準：
- `threads --help` 要能一眼看到所有能力
- `CLAUDE.md` 要寫清楚「這個專案有哪些工具、每個工具什麼時候用」
- 範例要能直接複製執行，不要有 `<your-token-here>` 這種佔位符要填

**品味判斷**：新來的 Agent（沒看過這專案）讀完 `CLAUDE.md` 能不能獨立操作？不能的話，缺什麼？

---

## 核心：這五條原則就是「系統設計的品味」

品味的核心是**問對問題**：

1. **哪些操作會犯錯？** → dry-run
2. **使用者要做決策前需要什麼事實？** → 狀態查詢
3. **錯了之後能不能自救？** → 錯誤訊息設計
4. **新人（或新 Agent）能不能獨立上手？** → 文件

這些問題跟用的語言、框架、AI 模型**都無關**。
- 會寫碼不保證會問這些問題
- 不會寫碼也可以學會問這些問題

未來做任何工具（Notion 外掛、選股工具、攝影後製腳本）都能套用。

---

## 對 threads_pipeline 的具體可做項目（備忘）

如果要用這專案當訓練場練品味，按順序建議：

1. **盤點 `CLAUDE.md` 是否 Agent-readable**：新 Agent 讀完能不能獨立操作？
2. **補 `threads status` 指令**：一口氣顯示 Token 狀態、DB 最近更新、上次 pipeline 跑的時間
3. **盤點錯誤訊息**：列出所有會丟錯誤的地方，補上「下一步建議」
4. **做 `tasks.py` 或 Makefile**：把 Agent 常用指令集中管理，同時成為「指令地圖」

（不急著做，討論完 C/D/E 再回頭挑）

---

## 為什麼這比寫碼能力更長遠

- AI 會越來越會寫碼，語法層級的能力會貶值
- 但**「什麼該做成工具、介面怎麼分、什麼該自動化」的判斷**不會
- 這種判斷來自大量「使用 → 感受痛點 → 設計解法」的循環
- 每次跟 Agent 協作時感覺到卡卡的，就是培養品味的素材

---

## 相關筆記

- `docs/lessons/data-is-information.md` — 資料、格式、程式的本質
- （未來）`docs/lessons/agent-first-products.md` — C/D/E 討論完整合
