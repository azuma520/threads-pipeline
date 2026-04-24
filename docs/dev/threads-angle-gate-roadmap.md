# threads-angle-gate 優化 Roadmap

> 第 1 層 skill 未來可能的優化清單。初版來自 2026-04-24 skill-creator audit，之後實測/回饋發現會持續 append。

## 關連檔案

- Skill: `skills/threads-angle-gate/SKILL.md`
- 設計 SSOT: `docs/dev/ak-threads-booster-research.md` 「選角度 Gate 設計定稿（v6，2026-04-23）」章節
- 首次測試紀錄: `docs/handoffs/session-handoff-20260424.md` Session 08:21

## 2026-04-24 skill-creator audit findings

### P1 建議做

#### 1. 存 `evals/evals.json`

把 2026-04-24 的 subagent 測試 case 結構化留存，未來 skill refactor 後可跑 regression test。

**包含**：
- Baseline（無 skill）+ with-skill v1 + with-skill v2 三次的輸入 prompt
- 各次的 PASS/FAIL 判準（四條強化規則：no assertion / no soft-assertion / Turn 1 一題 / source label 明示 phrase）

**Schema**：見 skill-creator `references/schemas.md`

**Trigger 時機**：下次真的要改 skill 之前，先建這份檔就地跑回歸。

### P2 可選

#### 2. 把 `angle.md` 產出格式抽成 `references/angle-template.md`

YAML template 和三種 `source` 值說明目前 inline 在 SKILL.md。現尺寸 253 行還 OK（spec <500 行），未來兩種 trigger 任一發生再拆：
- SKILL.md 逼近 400 行
- 真實跑過 3+ 次、有代表性 example angle.md 素材可放

#### 3. `references/example-angle.md`

一份完整填好的 angle.md 範例（真實 post 走過 gate 的產出），讓 Claude 更清楚什麼叫「好的共創切入點」。

**Trigger 時機**：跑 ≥ 3 次後挑最代表性的（尤其 `source: co_created` 那種）放進 `references/`。硬編沒意義、反而污染。

### P3 知情（不改，但心中有數）

#### 4. Description 風格張力

`superpowers:writing-skills` 派 vs `skill-creator` 派對 description 寫法有歧見：
- **writing-skills**：description 只寫 triggering conditions（怕 Claude 讀 description 就跳過 body）
- **skill-creator**：description 寫 both what + when，且要 pushy

目前 skill 偏 writing-skills 派。若未來觀察到 under-trigger（應該用 skill 的情境 Claude 沒用），可嘗試 skill-creator 的 pushy 風格。

改 description 之前建議先用 skill-creator 的 `run_loop.py` 跑 triggering eval 再動，避免憑感覺改退步。

---

## 實測後可能浮現的待辦（未觸發）

### 使用體感類（等真實用過幾次才知）

- Turn 1 節奏規範是否過嚴（真實對話可能需要鋪墊句，不全是問句）
- 四透鏡內部掃描是否自我污染（AI 在腦中分析時是否影響回話品質）
- Override 邊界判定（使用者說「我大概知道想寫什麼」算不算 Override？現在邊界模糊）
- 對話紀錄 truncate 策略（現 placeholder「完整問答紀錄」太模糊，長對話實作時才需決定）

### 多次實測後才出得來的

- `co_created` 比例追蹤機制（v6 說是 gate 健康度指標，但無工具收集）
- Override 篇 vs gate 篇表現對照（需 `insights_tracker` 接這維度）
- 不同題型的 gate 體感差異（技術分享 / 心情 / 專案事件 是否需要子 variant）

### 與其他層的接點（依賴未落地）

- **第 2 層 `planner.py`** 吃 `angle.md`：CLI flag 還是讀檔慣例（`drafts/<slug>.angle.md`）？等第 2 層升級時決定。
- **候選點 #1 Semantic Freshness Gate**：讓 AI 能帶「你過去寫過類似的角度」進場，屬於「雙向萃取」的 ai_observation 強化。
- **第 4 層 AI 防味**：若命中「可能抄了 gate 對話結構」這種 pattern，第 1 層對話紀錄的保留策略要兼容。

---

## 更新規則

每次實測 / refactor 後：

1. **發現新問題** → append 到「實測後可能浮現的待辦」對應分類，標 status
2. **Refactor skill** → append 一筆 iteration log（格式見下）
3. **待辦變緊急** → 升級 P0 / P1，寫進當日 handoff 的 next action
4. **待辦完成** → 從 roadmap 移除，短結論寫進該日 handoff「三、洞見紀錄」

### Iteration log 格式

```markdown
## Iteration YYYY-MM-DD

- **Trigger**: [實測 / audit / user feedback / regression]
- **Change**: [具體改了什麼]
- **Test**: [是否跑 RED-GREEN-REFACTOR / 是否有 evals/evals.json]
- **Handoff**: [連到當日 handoff Session 區塊]
```
