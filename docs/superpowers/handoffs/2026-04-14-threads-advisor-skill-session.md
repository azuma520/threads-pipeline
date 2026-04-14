# Handoff — threads-advisor skill 建立 + 第一次實戰測試

> 日期：2026-04-14
> 狀態：skill 草稿已完成、第一次實戰（用 skill 寫這次經驗的 Thread）進行中，卡在 [錯誤歸因] 段
> 下一個 session 要從這份文檔開始，不要重來 brainstorm。

---

## 1. 本次 session 做的事

### Repo 整理
- 個人參考材料（PDF、temp_pdf/、參考文檔）搬到 `.reference/`（gitignored）
- cache 資料夾搬到 `.reference/cleanup/`（待確認後手動刪）
- `.gitignore` 調整：放行 `.claude/skills/` 與 `.claude/agents/`

### 盤點文檔
- `docs/dev/capabilities-inventory.md`：專案四層能力 + 外部引用

### Skill 建立：`threads-advisor`
放兩份同步版本：
- `.claude/skills/threads-advisor/`（Claude Code 本機載入用）
- `skills/threads-advisor/`（repo 發佈用）

**檔案結構**：
```
threads-advisor/
├── SKILL.md                            # 觸發 + 四路徑 + CLI 手冊 + Token/Access Gate
└── references/
    ├── writing-philosophy.md           # 最上層：分享者不是教學者、誠實、節制、不討好
    ├── content-structure.md            # 認知翻轉鏈 + 5 種結構
    └── voice-patterns.md               # 短句節奏、情緒標點、禁用詞
```

**四條路徑**：
- **A. Plan**（寫新串文）：plan CLI + 5 類型互動分析 + **Step 5 寫完整草稿（必讀 3 份 reference）**
- **B. Topic Mining**（找靈感）：analyze + Claude 即席生成 10 題
- **C. Review**（審草稿）：review CLI
- **D. Diagnose**（觸及低）：analyze + threads-algorithm-skill

---

## 2. PR 狀態

- Branch：`feat/advisor-plan`，已 push
- PR：https://github.com/azuma520/threads-pipeline/pull/1
- 標題：feat(advisor): plan 串文骨架生成器 + threads-advisor skill
- 合進 main 前要先完成下列測試

---

## 3. 第一次實戰測試 — Thread 寫作進度

### 測試題目
「從『我想要發文助手』到 skill 上線：做給自己用的 AI 工具，三個意外發現」

### 決定的框架
#11 逆襲引流（認知翻轉鏈）

### 角色
- 受眾：其他開發者
- 目的：分享經驗
- 人格：Azuma 本人的寫作風格（分享者、飽滿、誠實、不討好）

### 三個意外定案
1. **Prompt ≠ 工作流**（場景：貼文檔給 Claude → 被告知要做工程設計 → 傻眼）
2. **知識資產不會自動接上**（場景：設計時差點忘了用自己做的 threads-algorithm-skill）
3. **上線不是終點，是第一次測試**（meta：這篇 Thread 本身就是 skill 第一次實戰）

### 目前已完成的貼文（尚未 voice 校準到位）

已經寫過初稿但**必須用新 workflow 重寫**（加進 writing-philosophy + content-structure + voice-patterns 後）：
- P1 主貼
- P2 痛點背景（**待決**：要不要砍）
- P3 第一次翻轉場景（貼文檔 → Claude 說要工程設計 → 傻眼 → 好吧那就設計吧）
- P4 轉場短橋（開始盤點）
- P5 意外 ②：差點忘了知識庫
- P6 意外 ③：meta 上線測試
- P7 工具長相（設計意圖：引導寫作的幫手，不是發文機器）

### 🔴 當前卡點 — 兩個缺口

**缺口 A：[錯誤歸因]（認知翻轉鏈必備環節，目前沒寫）**

被 Claude 打臉的瞬間，使用者**第一反應**怎麼解讀這件事？通常是錯的、但讓讀者共鳴。
候選：
- 覺得 Claude 太龜毛，想換 AI 試
- 覺得那份文檔其實吹牛
- 覺得自己沒讀清楚，應該先 review 一次
- 覺得專案做得不夠成熟難怪接不起來
- 其他

👉 **下一個 session 第一件事：問使用者這題**

**缺口 B：[開放結尾] P8**

留一個問題給讀者（認知翻轉鏈的收尾規則）。plan.md 原建議：「你有沒有哪個工作流是明知道可以自動化但一直沒動手的？」可以直接用或換。

---

## 4. 待補資源

### ❌ `references/writing-examples.md` — 範例五「我是一個將死之人」
使用者提過這是語氣終極校準錨點，但**還沒貼原文進 skill**。
下個 session 可以先問：「範例五的原文方便貼一下嗎？我存成 writing-examples.md 以後寫作都對它校準」

---

## 5. 語氣踩雷紀錄（重要！）

本次 session 多次寫出太 AI 的草稿，使用者糾正後抓到的規則：

1. **不要下教訓**：寫完故事就結束，不要補「所以我學到了」「這告訴我們」「值得反思」
2. **不要 meta 反思**：「讓我傻眼的不是 X，是 Y 這件事」這種反身結構 = 說教
3. **不用過渡句**：不要「接下來」「說完了 A，讓我們看 B」，直接跳
4. **不用 `——`（雙破折號）太多**：偶爾可以，不是主力
5. **句子要短**：在呼吸點斷，不在文法點斷，每行 5-15 字
6. **情緒標點直接用**：「煩死了!!!」「欸？」「哎呦」「=_=」不要含蓄
7. **內心戲用引號**：「我心想：...」不要間接敘述
8. **自嘲**：「我是個...新手」「哎呀」而不是「不過我還有進步空間」

> **終極校準**：問「範例五『我是一個將死之人』那個人會這樣講話嗎？」不會就重寫。

---

## 6. 建議的 session 開場

1. 讀本份 handoff
2. 確認使用者有沒有要貼「範例五」原文
3. 問 [錯誤歸因] 那題
4. 重讀 `.claude/skills/threads-advisor/references/` 三份 reference
5. **用新 workflow 重寫 P1-P7**（一次交出來給使用者看，不要一條一條討論節奏太慢）
6. 寫 P8 CTA
7. 完成後 commit、Push、回到 PR #1

---

## 7. 不要做的事（避免重蹈覆轍）

- ❌ 不要再花一輪 brainstorm 重新問使用者「skill 要做什麼」—— 答案在這份 handoff 和 capabilities-inventory.md
- ❌ 不要一條一條貼文反覆迭代 —— 使用者會頭痛，整組寫好再交
- ❌ 不要加狀態表、彩色標記、分段 badge（「✅ 確定」「🔴 未定」）—— 使用者說過讓他頭痛
- ❌ 不要寫 meta 自我反思類的「洞察」—— 使用者明確不喜歡說教
- ❌ 不要沿用「⸻」這種分隔符 —— 那是 AI 排版慣性

---

## 8. Repo 當前狀態

```
Branch: feat/advisor-plan（領先 main 23 commits，PR #1 open）

最近 commits：
  ae4af46 feat(skill): threads-advisor 加 writing-philosophy.md（最上層哲學）
  e7e3b85 feat(skill): threads-advisor 加 content-structure + voice-patterns 參考檔
  be6c9af feat(skill): threads-advisor Path A Step 4 加 5 類型互動分析
  5133656 feat(skill): threads-advisor skill draft + gitignore adjustment
  d04a67f docs: capabilities inventory (Layer 1-4 + external references)
  8d2c29b chore: gitignore personal reference materials (.reference/)

drafts/：有一個 plan.md（這次題目的骨架）
  從『我想要發文助手』到-skill-上線.plan.md
```
