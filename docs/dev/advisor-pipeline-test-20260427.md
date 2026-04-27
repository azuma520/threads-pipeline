# Advisor Pipeline 實測報告 — 2026-04-27

## 測試目標

驗證 `docs/dev/advisor-pipeline-schema.md` 的 schema + Gate checklist 對「AI 跑 advisor 流程」的實際約束力。

具體要測：
1. **Artifact schema** 能不能逼出完整產物（vs 0424 18:07 的半套 plan.md）
2. **Stage gate checklist** 能不能擋住跳步驟（vs 0424 18:07 的 Step 2-4 全跳）
3. **Reference dependency check** 能不能擋住反序讀（vs 0424 18:07 的 voice→content→philosophy 反序）
4. **Voice self-check** 能不能擋住 self-deprecation（vs 0424 18:07 的「沒什麼特別的方法」）

## 測試對象

`drafts/ai-tool-reflection-rhythm.*` 全套，**從 Stage 1 重做**（Stage 0 angle.md 已 Gate 0→1 PASS，不重訪談）。

## 測試方法

- 每個 stage 完整執行：mimic CLI（如需）+ 產 artifact + 跑 Gate checklist
- Stage 結束**停**，user hold 紀律 review，AI 記錄 observation
- 不真發文（Stage 7 dry-run 為止）

## 環境

- Branch: main（advisor-plan branch CLI 不可用，Stage 1/2 用 mimic）
- 已知工具：threads-angle-gate ✅ / advisor review ✅ / threads post ✅ / advisor plan ⚠️ branch
- AI: Claude Opus 4.7（本 session）
- User: hold 紀律的「管理者」角色（0424 18:07 母題）

---

## Stage 0 結果（Carry-over）

**Status**: ✅ PASS（0424 17:18 已驗）
**Artifact**: `drafts/ai-tool-reflection-rhythm.angle.md`
**不重做原因**: Gate 0→1 已 PASS，重訪談會 re-open 角度而非測試 pipeline

---

## Stage 1 — Framework 建議

**Status**: WAIT (Gate 1→2 FAIL after Pattern B replay)

**Artifact**: `drafts/ai-tool-reflection-rhythm.framework.md`（mimic CLI 產出，含 3 個 considered framework + 推薦排序，chosen 欄位待 user 選）

**Gate 1→2 Replay Results**（用 Pattern B-1/B-3/B-4 強化後的 schema 重驗）：

| Checkbox | Status | Evidence |
|----------|--------|----------|
| `framework.md` 存在 | ✅ | confirmed |
| 列出 3 個 considered framework | ✅ | 07 PREP / 14 感性觀點 / 04 SCQA + 推薦排序 |
| `chosen_framework.id` ∈ 16+1 清單 | ❌ | `id: ?`（空） |
| `chosen_reason` 非空 | ❌ | `chosen_reason: ?`（空） |
| User align「這個框架對嗎」 | ❌ | 本 session 未確認 |

**Gate verdict**: FAIL (3/5 checkboxes fail) → Stage 2 BLOCKED

**Plan Failures 命中**：
- `chosen_framework 仍為 ? 或空（user 未選定卻聲稱 Gate PASS）` ✅
- `chosen_reason 為空` ✅

**Pattern B 有效性驗證**：
- B-1 REQUIRED NEXT STEP：✅ 擋住 Stage 2 entry（任一 checkbox 未勾 = 不得進下一 Stage）
- B-3 Plan Failures：✅ 具體規則 fire，引用 schema 原文
- B-4 Iron Law：✅ Common Failures table「user 0424 選過 PREP 不算 Stage 1 done」精準命中——記憶 ≠ artifact，必須在本 session 重驗

**Conclusion**：今天的工程化（Iron Law + Plan Failures + REQUIRED NEXT STEP）對「Gate 紀律」這層 enforcement 有效。下一步驗證在新 session：跑完整 advisor Path A 流程，看多回合 drift 場景是否仍守得住。

---

## Stage 2 — Plan 骨架

（尚未開始）

---

## Stage 3 — 演算法整合

（尚未開始）

---

## Stage 4 — 互動設計

（尚未開始）

---

## Stage 5 — Draft 草稿

（尚未開始）

---

## Stage 6 — Review

（尚未開始）

---

## 彙整 Findings

（測試結束後 append）
