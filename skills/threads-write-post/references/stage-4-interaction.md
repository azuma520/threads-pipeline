# Stage 4 — Interaction design（互動元素配置）

> **進入 Stage 4 時讀本份 reference in full**。互動類型、數量規則與 example_phrasing 規範必須對齊本份。

---

## 這個 stage 在做什麼

Stage 4 決定整個 thread 要放幾個互動元素、放在哪幾條 post、每個用什麼類型。輸出是「互動配置」，不是寫好的互動語句——但必須給出 `example_phrasing` 作為 Stage 5 寫稿時的 hint，否則 Stage 5 無從下筆。

---

## 5 種互動類型（封閉清單）

| 類型 | 描述 | 適合場景 |
|---|---|---|
| **開放式問題** | 邀讀者用自己語言回答（非 yes/no） | 想引發實質留言、收集多元觀點 |
| **爭議觀點** | 拋出可能引發不同意的立場 | 想拉討論熱度（風險：拉錯方向變筆戰） |
| **個人經驗邀請** | 「你有沒有 X 過」「你的 Y 是怎樣」 | 想讓讀者帶自己故事進來 |
| **投票選擇題** | 二選一 / 多選一 | 想低門檻互動、收集偏好 |
| **標記朋友** | 「tag 一個 X 的朋友」 | 想擴散到圈外 |

**只能從這 5 類型選**——自創類型 = Gate FAIL。

---

## 數量規則

整串 thread 的 `chosen_types` 數量必須是 **2 或 3**：

- 1 個 = 過少。Threads 平台特性下單一互動拉不動討論深度。
- 4+ 個 = 過密。讀者壓力過大、互動意願下降、像問卷不像分享。
- 2–3 個 = 甜蜜點。

`chosen_types` 中也不該重複——例如同一串放兩次「開放式問題」=1 種類型用 2 次，仍視為 1 種，數量不夠。

---

## Stage 4 Artifact Schema

**檔名**：`drafts/<slug>.interaction.md`

**必填欄位**：

```yaml
stage_entry_announced: true
upstream_gate_passed: true

chosen_types:
  - type: "開放式問題"
    post_position: "P3"
    why_this_post: "P3 是 plan 中『轉』的位置，讀者剛被反直覺命題鬆動信念，最適合邀請他用自己語言重新表達"
    example_phrasing: "你最近有沒有遇到 X 的時候會這樣想的？"

  - type: "個人經驗邀請"
    post_position: "P5"
    why_this_post: "P5 是收尾，邀請讀者帶自己故事進留言區，比制式 CTA 更貼合本篇『分享而非推銷』的 voice"
    example_phrasing: "你自己 Y 過嗎？怎麼處理？"
```

---

## 規則

- `chosen_types` 數量 ∈ {2, 3}（**不接受 1 個或 4+**）
- 每個 chosen type 的 `post_position` 必須對應 plan.md 骨架實際存在的 post（不能放到不存在的 P9）
- `why_this_post` 不可為空、不可寫「適合」「自然」這類空話。要具體說「為什麼這條 post 最適合這個互動類型」（跟 plan 的起承轉合 mapping 對齊）
- `example_phrasing` 不可為空——Stage 5 要靠這個 hint 寫互動句。空 = Gate FAIL
- `example_phrasing` 是 hint **不是成稿**。一兩句示範句即可，正式句子在 Stage 5 寫
- `chosen_types` 內 `type` 欄位必須是 5 類型之一（**不接受自創**）

---

## 設計 trade-off 提醒

- **爭議觀點高風險**：能拉熱度也能拉錯方向。除非 angle.md 的 sharpness 本身就帶爭議，否則小心使用。
- **標記朋友低品質**：擴散度高但 deep engagement 低；Threads 演算法可能視為 Low Signal（見 stage-3-algo.md `avoid_mechanisms`）。除非清楚誘因，否則少用。
- **投票選擇題**：低門檻好用，但連續多篇都用會顯得 Buzzfeed 化。一篇放 1 個就夠。
- **開放式問題 + 個人經驗邀請**通常是最穩的組合（有實質內容 + 邀請帶故事），對齊本 pipeline「分享自己而非推銷自己」的內容哲學。

---

## Plan Failures（含以下任一即 Gate 4→5 FAIL）

- `chosen_types` 數量 ∉ {2, 3}（1 個過少；4+ 過密）
- 任一 chosen type 的 `post_position` 與 plan.md 骨架不對應
- `why_this_post` 為空或寫空話
- `example_phrasing` 為空（Stage 5 將無從寫起）
- 5 類型清單外的自創類型（必須來自 schema 規定的 5 類型）

---

## Gate 4 → 5 Checklist

進 Stage 5 前，本訊息逐條跑：

- [ ] `drafts/<slug>.interaction.md` 存在
- [ ] `chosen_types` 數量 ∈ {2, 3}
- [ ] 每個都有 `post_position` 標明放在哪條 + 對應 plan 實際 post
- [ ] 每個 `why_this_post` 非空且不是空話
- [ ] 每個 `example_phrasing` 非空（Stage 5 要靠這個 hint）
- [ ] 所有 type 都在 5 類型清單內（無自創）
- [ ] **User align**：「互動設計對嗎」明確發生於本 session

任一未勾 = Gate FAIL = **不得**進 Stage 5。
