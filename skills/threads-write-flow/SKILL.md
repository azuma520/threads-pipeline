---
name: threads-write-flow
description: "Use when the user wants to write a Threads post end-to-end starting from raw dump (no pre-existing angle) — dump-first workflow with 10 steps: dump → main thread → interview supplement → diagnosis → narrative draft → hooks → user calibration → finalize → anti-template → versions. Triggers: user says 「我有東西想寫但還沒想清楚」/「幫我從原始素材寫文」/「跑寫文工作流」/「我要寫 Threads 但沒 angle」, dumps raw material without a pre-locked angle. PREREQUISITE: none (Step 1 accepts raw dump). Do NOT use when user has a locked angle.md — use threads-write-post v2 (which starts from angle). Do NOT use for Stage 0 angle decisions if user is still unsure — use threads-angle-gate first."
---

# threads-write-flow — Threads 貼文寫作 pipeline（Step 1→9，dump-first）

## 這個 skill 是什麼

從 user 的**原始 dump**（沒有預先 lock 好的 angle）出發、走 10 step 把貼文寫到能發出去：

1. **原始材料輸入**（user dump、AI 不打斷）
2. **核心主線整理**（AI 抓 4 件事 + 綁原文錨點）
2.5 **訪談補充**（諮詢式問法 + 5 條素材檢查 + 沒有就沒有）
3. **原文優點與弱點診斷**（對照 user 表達特徵 4.1/4.2）
4. **初步結構重排**（敘事草稿 + 編排理由 + 不確定點）
5. **鉤子與切入點挖掘**（3-5 個切入點 + 5 維度評估）
6. **使用者 sense 校準**（user 是總編輯、5 情境校準表）
7. **最終修文**（reference 紅旗座標）
8. **反模板化檢查**（3 句 sense self-prompt + user 對齊）
9. **可選發文版本輸出**（短版 / 長版 / 多平台）

**跟 `threads-write-post` v2 的差別**：v2 從已 lock 的 `angle.md` 接 Stage 1（選框架）；本 skill 從**原始 dump** 開始，前置不需要 angle.md。兩個 skill 並存、user 視情境選用。

**Spec source of truth**：`docs/superpowers/specs/2026-05-06-write-flow-skill-design.md`（v2.1.1）。

---

## Pipeline Iron Law（凌駕全文件，跨 step 適用）

```
NO STEP PROGRESSION WITHOUT FRESH GATE EVIDENCE.
```

If you haven't checked the Gate checklist in **this message**, you cannot claim Step N is complete. **Spirit over letter** — finding a loophole in the wording is still a violation.

### Gate Function（每進下一 Step 前必跑）

1. **IDENTIFY**：上一 Step 的 Gate 是哪一條（Gate N→N+1）？
2. **READ**：對應 reference doc 的 Gate 段（`references/step-XX-*.md` 的 Gate 章節）── **必須 fresh read in this message**，不能引用之前 turn 的記憶
3. **CHECK**：對照當前 step 的 artifact，每一條 Gate criterion 都過了嗎？
4. **PROCEED or HOLD**：全過進下一 step；任一條沒過、停下、surface 給 user。

**Anti-cheat phrase**（每進下一 step 前都要在訊息中明確講）：「**Gate N→N+1 fresh read evidence: [引用 reference 的具體段]、[列每條 criterion 的 pass/fail]**」── 沒講這句不算過 Gate。
