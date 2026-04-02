# V2.5 貼文健檢（發文顧問）設計規格

## 目標

在發文前提供數據驅動的策略建議和草稿審查，結合演算法知識 + 文案結構框架 + 歷史表現數據，幫助使用者寫出更有共鳴的貼文。

## 核心理念

「分享自己，不是推銷自己。」工具輔助判斷，不取代創作者的聲音。

## 產品定位

- **V2.5（現在）**：只用自家歷史內容與帳號成效做分析，不含外部市場洞察
- **Advanced Access 後**：加入外部熱門貼文與競品對照

---

## 使用流程

```
Step 1: advisor analyze
  → 從 SQLite 撈數據，產出帳號分析報告（純 Python）

Step 2: /threads-algorithm-skill 互動討論
  → 讀取分析報告，討論主題、受眾、痛點、建議結構
  → 產出 plan.md（Claude）

Step 3: 使用者根據 plan 寫草稿 → draft.txt

Step 4: advisor review draft.txt
  → 對照 plan + 數據 + 演算法知識 + 文案框架審查
  → 輸出評分 + 改進建議（Codex CLI）
```

---

## 元件分工

| 元件 | 指令 | 職責 | 技術 |
|------|------|------|------|
| 數據分析 | `advisor analyze` | 撈 SQLite、算歷史模式、對齊演算法框架 | 純 Python |
| 發文規劃 | `/threads-algorithm-skill` | 討論受眾、痛點、切入角度、推薦文案結構 | Claude Skill 互動 |
| 草稿審查 | `advisor review draft.txt` | 對照受眾 + 數據 + 演算法 + 文案結構評分 | Codex CLI subprocess |

---

## Schema 擴充（前置作業）

在現有 `insights_tracker.py` 的 `post_insights` 表新增欄位：

```sql
ALTER TABLE post_insights ADD COLUMN full_text TEXT;
ALTER TABLE post_insights ADD COLUMN post_hour_local INTEGER;
ALTER TABLE post_insights ADD COLUMN author_reply_count INTEGER DEFAULT 0;
```

| 欄位 | 來源 | 用途 |
|------|------|------|
| `full_text` | `me/threads` API 的 `text` 欄位 | 內容特徵分析、定位判斷 |
| `post_hour_local` | `posted_at` 轉換為 Asia/Taipei 的小時數 | 發文時段分析 |
| `author_reply_count` | `{post_id}/replies` 中 `username == 自己` 的數量 | 回覆互動習慣分析 |

同時抽出共用模組 `db_helpers.py`，讓 `insights_tracker.py` 和 `advisor.py` 共用 config loading、DB 連線、基礎查詢。

---

## 數據分析報告（advisor analyze）

從 SQLite 撈數據，對齊 threads-algorithm-skill 的演算法框架，產出 Markdown 報告。

**原則：數據有多少就說多少，不用少量數據產出高確信結論。**

### 報告結構

```markdown
# 發文策略分析報告 — YYYY-MM-DD

## 帳號現況
- 粉絲數 / 近 7 天觀看 / 粉絲變化

## Creator Embedding 觀察（account-authority）
- Top 5 高表現貼文的共同特徵（從 full_text 提取關鍵字）
- Top 5 低表現貼文的共同特徵
- 觀察：你的高表現內容傾向 [特徵描述]

## Distribution Lifecycle 分析（distribution-lifecycle）
- 上一篇發文時間 + 表現
- Freshness 狀態（距今幾天）
- 自打風險評估（< 24hr 有風險）
- 歷史高表現貼文的發文時段分布（post_hour_local 統計）

## Engagement Economics 分析（engagement-economics）
- 平均互動率（views > 0 的貼文）
- 回覆 / 按讚 / 轉發佔比
- 作者回覆率：平均每篇回覆 N 則（author_reply_count）
- 作者回覆率 vs 互動率的相關觀察

## 歷史表現 Top 5
| 內容摘要 | 觀看 | 互動率 | 作者回覆數 | 發文時段 |

## 數據摘要（供審查用，JSON 格式）
{
  "followers": 206,
  "avg_engagement_rate": 2.4,
  "top_post_hours": [18, 19, 20],
  "top_content_keywords": ["AI", "經驗分享", "工具"],
  "avg_author_replies": 8,
  "last_post_days_ago": 4,
  "freshness": "expired"
}
```

### 三種運作模式

| 模式 | 條件 | 輸出 |
|------|------|------|
| 正常模式 | >= 7 天數據 | 完整報告 |
| 降級模式 | 1-6 天數據 | 只輸出帳號現況 + Top 貼文，標注「數據累積中」 |
| 無資料模式 | 0 天數據 | 提示「請先執行 Pipeline 收集數據」，不做分析 |

### 數據來源

- `post_insights` 表：views, likes, replies, reposts, quotes, posted_at, full_text, post_hour_local, author_reply_count
- `account_insights` 表：followers, total_views, collected_date
- 計算欄位：互動率、回覆佔比、發文間隔、時段分布

### 輸出

- 完整報告：`output/advisor/analysis_YYYY-MM-DD.md`
- 審查摘要：`output/advisor/analysis_YYYY-MM-DD.json`（review 只讀這個，控制 prompt 長度）

---

## 發文規劃（/threads-algorithm-skill 互動）

使用者給一個主題，Claude 透過互動討論產出 plan。

### 討論流程

1. **主題確認**：你想寫什麼？
2. **受眾設定**：這篇要寫給誰？他們的痛點是什麼？
3. **切入角度**：根據歷史高表現特徵和受眾，建議怎麼切
4. **結構推薦**：根據主題和受眾，從 16+1 結構中推薦最適合的 1-2 個
5. **大綱建議**：按照推薦結構，給出每段的方向

### Plan 輸出格式（最低必要 schema）

```markdown
---
topic_id: ai-agent-automation
analysis_date: 2026-04-02
created_at: 2026-04-02T10:30:00
---

# 發文規劃 — AI Agent 自動化

## 目標受眾
- 誰：[受眾描述]（必填）
- 痛點：[他們在乎什麼]（必填）
- 期望收穫：[看完能帶走什麼]（必填）

## 建議結構
- 推薦：[結構名稱]（必填）
- 原因：[為什麼這個結構適合]

## 大綱
1. [結構第一段] — [方向建議]（必填，至少 2 段）
2. [結構第二段] — [方向建議]
3. [結構第三段] — [方向建議]
4. [結尾類型] — [互動式 / 夥伴式 / Slogan / 反轉式]

## 注意事項
- [根據演算法知識的提醒]
- [根據歷史數據的提醒]
```

### 檔案命名

- 檔名用 slug：`drafts/{topic_id}.plan.md`（不用中文檔名）
- 原始主題標題放在 frontmatter 和 heading 中
- topic_id 規則：小寫英文 + 連字號，例如 `ai-agent-automation`

---

## 草稿審查（advisor review）

用 Codex CLI 審查草稿，帶入分析摘要 + plan + 演算法知識 + 文案框架作為 context。

### 呼叫方式

```bash
# 主要用法：讀取檔案，自動找同名 plan
python -m threads_pipeline.advisor review drafts/ai-agent-automation.txt

# 明確指定 plan 和 analysis
python -m threads_pipeline.advisor review drafts/my-post.txt \
  --plan drafts/ai-agent-automation.plan.md \
  --analysis output/advisor/analysis_2026-04-02.json

# 也支援直接輸入（短文用）
python -m threads_pipeline.advisor review --text "短草稿"
```

### 檔案關聯機制

1. 草稿 `drafts/{topic_id}.txt`
2. 自動尋找同 topic_id 的 plan：`drafts/{topic_id}.plan.md`
3. 自動尋找最新 analysis JSON：`output/advisor/analysis_*.json`
4. 找不到 plan → 仍可審查，但跳過「受眾匹配」維度
5. 找不到 analysis → 仍可審查，但跳過數據相關維度
6. 支援 `--plan` 和 `--analysis` 明確覆寫

### Codex CLI Subprocess Contract

```
指令：codex exec -s read-only -o {output_path} "{prompt}"
Timeout：60 秒
Retry：失敗時重試 1 次
Output：寫入 drafts/{topic_id}.review.md
Exit code 非 0：記錄 stderr，輸出「審查失敗，請手動檢查」
UTF-8：所有 I/O 強制 UTF-8
Prompt 上限：控制在 8000 字以內（analysis 用 JSON 摘要版）
```

### 內部流程

```
1. 讀取草稿檔案
2. 讀取分析摘要 JSON（output/advisor/analysis_YYYY-MM-DD.json）
3. 讀取對應的 plan（如果存在）
4. 讀取演算法知識摘要（精簡版，不是完整 reference）
5. 讀取文案結構框架摘要
6. 組合 prompt（控制 < 8000 字）
7. 呼叫 codex exec subprocess
8. 寫入 drafts/{topic_id}.review.md
```

### 審查評分維度（6 項）

| 維度 | 對應機制 | 判斷依據 |
|------|---------|---------|
| 鉤子 | Low Signal 篩選 | 前兩行能不能讓人停下來（前 3 秒抓住眼球） |
| 聚焦度 | Creator Embedding | 一篇一個切入點、一種人、一個問題 |
| Takeaway | Engagement Economics | 讀完能帶走什麼，會不會想回覆 |
| 定位一致性 | Creator Embedding | 跟歷史高表現貼文的關鍵字是否一致 |
| 受眾匹配 | Audience Affinity | 有沒有打中 plan 設定的受眾痛點（需要 plan） |
| 結構完整性 | 文案框架 | 是否符合所選結構的要素，結尾是否有力（需要 plan） |

### 輸出格式

```
整體評分：⭐⭐⭐⭐ (4/5)

✅ 鉤子 — 開頭用個人經驗切入，會讓人停下來
✅ 聚焦度 — 一篇一個主題，不發散
⚠️ Takeaway — 結尾可以更明確，讀者看完能帶走什麼
✅ 定位一致性 — 符合歷史高表現的 AI 工具 + 個人經驗方向
✅ 受眾匹配 — 切中「想用 AI 但不知從何下手」的痛點
⚠️ 結構完整性 — 使用 SCQA 結構但缺少明確的 Q（問題）段

建議行動：
1. 最後一段加一句具體的 takeaway
2. 在「衝突」和「答案」之間加一個明確的問題句
```

### 邊界處理

| 情境 | 處理 |
|------|------|
| analysis 不存在 | 跳過數據維度，只審查文案品質 |
| plan 不存在 | 跳過受眾匹配和結構完整性 |
| draft 為空 | 報錯中止 |
| draft 超過 2000 字 | 警告「過長，建議精簡」，仍然審查 |
| views = 0 的貼文 | 計算互動率時排除 |
| codex exec 失敗 | 輸出錯誤訊息，建議手動審查 |

---

## 文案結構框架（新增 reference）

將魏育平的 16+1 結構整理成 reference 檔案。

### 檔案位置

`references/copywriting-frameworks.md`（放在專案 repo 內，不依賴外部 skill）

### 16+1 結構清單

| # | 名稱 | 公式 | 適用場景 |
|---|------|-----|---------|
| 01 | 引爆行動 | 觀點 → 危害 → 論據 → 結論 | 想改變讀者行為 |
| 02 | 破案解謎 | 疑問 → 描述 → 案例 → 總結 | 解答常見困惑 |
| 03 | 挑戰類 | 挑戰主題 → 有趣情節 → 輸出價值 | 分享挑戰過程 |
| 04 | SCQA | 情境 → 衝突 → 問題 → 答案 | 解決具體問題 |
| 05 | 三步循環 | 提問 → 設概念 → 解釋概念 | 解釋新概念 |
| 06 | 目標落地 | 美好目標 → 達成條件 | 激勵行動 |
| 07 | PREP | Point → Reason → Example → Point | 表達明確觀點 |
| 08 | 對比 | 錯誤操作 → 負面結果 → 正確方法 → 正向結果 | 教學糾正 |
| 09 | FIRE | Fact → Interpret → Reaction → Ends | 評論時事/趨勢 |
| 10 | 爆款人設 | 炸裂開頭 → 人設信息 → 高密度信息點 → 互動結尾 | 自我介紹/品牌建立 |
| 11 | 逆襲引流 | 積極結果 → 獲得感 → 方案 → 互動結尾 | 分享成功經驗 |
| 12 | 金句 | 金句 → 佐證 → 金句 → 佐證 | 觀點輸出、金句洗腦 |
| 13 | 行業揭秘 | 行業揭秘 → 塑造期待 → 解決方案 | 分享內幕/專業知識 |
| 14 | 感性觀點 | 事實 → 感受 → 發現問題 → 結論 → 故事 → 總結 | 感性共鳴 |
| 15 | 通用類 | 鉤子開頭 → 塑造期待 → 解決方案 → 結尾 | 萬用結構 |
| 16 | 教知識經典 | 問題描述 → 問題拆解 → 答案描述 → 答案拆解 | 深度教學 |

### 4 類結尾

| 類型 | 特點 | 適用 |
|------|------|------|
| 互動式 | 引導留言、私訊、點讚 | 拉高互動數據 |
| 夥伴式 | 營造「我們是戰友」感 | 培養粉絲黏性 |
| Slogan | 品牌口號式收尾 | 品牌形象 |
| 反轉式 | 最後翻轉觀眾預期 | 記憶點 |

---

## 檔案結構

```
threads_pipeline/
├── advisor.py                          ← 新增：analyze + review
├── db_helpers.py                       ← 新增：共用 config/DB/查詢
├── drafts/                             ← 新增：草稿 + plan + review（gitignored）
│   ├── {topic_id}.plan.md
│   ├── {topic_id}.txt
│   └── {topic_id}.review.md
├── output/advisor/                     ← 新增：分析報告（gitignored）
│   ├── analysis_YYYY-MM-DD.md
│   └── analysis_YYYY-MM-DD.json
└── references/                         ← 新增：文案結構框架
    └── copywriting-frameworks.md
```

### 重構：共用模組 db_helpers.py

從 `main.py` 和 `insights_tracker.py` 抽出：
- `load_config()` — 已在 main.py，移到共用
- `get_db_connection(config)` — DB 連線（read-only 模式用 `uri=file:...?mode=ro`）
- `get_top_posts(conn, limit)` — 已在 insights_tracker.py
- `get_trend(conn)` — 已在 insights_tracker.py

`advisor.py` 和 `insights_tracker.py` 都 import 自 `db_helpers`。

---

## 未來擴充（Advanced Access 後）

- `analyze` 加入外部趨勢數據（公開貼文搜尋結果）
- `plan` 參考同領域熱門貼文的結構和切入角度
- `review` 跟同領域高表現貼文比對風格
- 新增 `advisor trending` 指令：顯示目前熱門話題 + 建議切入方式
- `review` 檢查「與近期自己貼文是否過度重複」

---

## 依賴

- 現有：SQLite（insights_tracker）、config.yaml
- 新增：Codex CLI（`codex`，已安裝 v0.115.0）
- 現有：threads-algorithm-skill（Claude Code Skill）

---

## Codex 第三方審查回饋（2026-04-02）

完整審查結果：`docs/superpowers/specs/2026-04-02-post-advisor-codex-review.md`

### 已解決的 P0/P1 問題

| 問題 | 解決方式 |
|------|---------|
| SQLite 數據不足 | 新增 full_text、post_hour_local、author_reply_count 欄位 |
| 最佳發文時段算法不可落地 | 改為「歷史高表現貼文的發文時段分布」 |
| draft/plan/analysis 關聯缺失 | 用 topic_id 關聯 + 支援 --plan/--analysis 覆寫 |
| Codex subprocess 規格不具體 | 定義 timeout、retry、output schema、錯誤處理 |
| plan 不可測試 | 定義 plan.md 最低必要 schema（frontmatter + 必填欄位）|
| 重複邏輯 | 抽出 db_helpers.py 共用模組 |
| 定位一致性百分比無數據支撐 | 改為定性觀察（高表現貼文共同特徵）|
| 冷啟動未定義 | 定義三種模式（正常/降級/無資料）|
| 檔名問題 | 用 slug 命名，原始標題放 frontmatter |
| Prompt 容量風險 | 拆成完整報告 + JSON 摘要，review 只讀摘要 |
