# Stage 3 — Algo mapping（演算法機制對應）

> **進入 Stage 3 時讀本份 reference in full**。**另需 consult global `threads-algorithm-skill`** 取得 26 機制清單原文。
>
> **重要**：26 機制清單**不在本 reference**。本份只說怎麼做 mapping、不複製清單，避免兩處 drift。每次 mapping 都從 `threads-algorithm-skill` 撈當下版本。

---

## 這個 stage 在做什麼

Stage 3 把 plan.md 的骨架對應到 Threads 演算法的 26 個機制——每條 post 主訴哪個機制、為什麼適用、有什麼 trade-off。整體層面再標出本篇主訴的 2–3 個 dominant 機制 + 刻意避開的機制。

目的不是「迎合演算法」，是讓骨架的影響力放大方向是有意識選擇。

---

## 必須 consult 的外部 skill

**`threads-algorithm-skill`**（global skill，由 `azuma520/threads-algorithm-skill` 維護）

進入 Stage 3 時必須讀過該 skill 的機制清單（26 個 Meta 演算法專利機制，含 Creator Embedding、Audience Affinity、Diversity Enforcement、Low Signal 偵測等）。

**規則**：機制名稱必須**逐字引用 `threads-algorithm-skill` 原文**。**禁止編造機制名**——例：「互動推進機制」「曝光放大機制」這種我自己造的名字 = Gate FAIL。

如果 skill 暫時不可用（plugin 沒載），本 stage **暫停**，不要用記憶或腦補的機制名繼續寫，回頭等 skill 可用再做。

---

## Stage 3 Artifact Schema

**檔名**：`drafts/<slug>.algo.md`

**必填欄位**：

```yaml
stage_entry_announced: true
upstream_gate_passed: true

# 每條 post 對應至少 1 個機制
post_mappings:
  - post_position: "P1"
    mechanism: "<原文機制名，引自 threads-algorithm-skill>"
    why_applies: "P1 用反直覺鉤子，觸發演算法對『高停留率訊號』的偏好（從 skill 第 X 條延伸推論）"
    risk: "若反直覺過於 edgy 可能被 Diversity Enforcement 抑制"
  - post_position: "P2"
    mechanism: "..."
    why_applies: "..."
    risk: "..."
  # ... P3, P4, ...

# 整體訴求
dominant_mechanisms:
  - "<原文機制名 1>"
  - "<原文機制名 2>"

avoid_mechanisms:
  - "Low Signal 偵測"   # 例：避免短回應/無實質內容
  - "<其他刻意避開的機制>"
```

---

## 規則

- **每條 post 至少對應 1 個機制**——可多但不能 0。
- **`mechanism` 必須引用 `threads-algorithm-skill` 原文**。原文沒有的名稱 = 編造 = Gate FAIL。
- `why_applies` 不可為空、不可寫「相關」「適合」「有幫助」這類空話。要具體說「這條 post 的哪個元素觸發這個機制」。
- `risk` 不可為空——每個機制都有 trade-off / 邊界條件 / 反作用。沒寫 = 沒思考 = Gate FAIL。
- `dominant_mechanisms` 必須跟每條 post 的 mechanism 列表**邏輯一致**（不能 dominant 了 X 但沒有任何一條 post 對應 X）。
- `avoid_mechanisms` 至少列 1 個（一般是 Low Signal / 制式 CTA / 過度自我推銷類）。

---

## Plan Failures（含以下任一即 Gate 3→4 FAIL）

- 任一 post 沒對應 mechanism
- mechanism 名稱**未引用 `threads-algorithm-skill` 原文**（編造視為違規）
- `why_applies` 為空或寫空話
- `risk` 為空（每個機制都有 trade-off，必須列）
- `dominant_mechanisms` 與每條 post mechanism 不相干（不一致）
- `avoid_mechanisms` 為空

---

## Gate 3 → 4 Checklist

進 Stage 4 前，本訊息逐條跑：

- [ ] `drafts/<slug>.algo.md` 存在
- [ ] 每條 post 對應 ≥ 1 個機制
- [ ] 機制名**全部來自 `threads-algorithm-skill` 26 機制清單**（編造視為 fail）
- [ ] 每個 mechanism 都有 `why_applies` 與 `risk` 非空
- [ ] `dominant_mechanisms`（2–3 個）邏輯上跟每條 post mechanism 一致
- [ ] `avoid_mechanisms` 至少 1 個
- [ ] **User align**：「演算法解讀對嗎」明確發生於本 session

任一未勾 = Gate FAIL = **不得**進 Stage 4。
