# Stage 1 — Framework pick

> **進入 Stage 1 時讀本份 reference in full**。16+1 框架公式必須引用原文，不可從記憶引用。
>
> **同步來源**：本份框架表 copy 自 `references/copywriting-frameworks.md`（advisor.py CLI 仍 import）。修改任何一邊請同步另一邊。

---

## 爆款文案腳本 16+1 結構

來源：魏育平（噯嚕嚕短影音行銷）課程簡報

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
| 12 | 金句 | 金句 → 佐證 → 金句 → 佐證 | 觀點輸出 |
| 13 | 行業揭秘 | 行業揭秘 → 塑造期待 → 解決方案 | 分享內幕/專業知識 |
| 14 | 感性觀點 | 事實 → 感受 → 發現問題 → 結論 → 故事 → 總結 | 感性共鳴 |
| 15 | 通用類 | 鉤子開頭 → 塑造期待 → 解決方案 → 結尾 | 萬用結構 |
| 16 | 教知識經典 | 問題描述 → 問題拆解 → 答案描述 → 答案拆解 | 深度教學 |

---

## 4 類結尾

| 類型 | 特點 | 適用 |
|------|------|------|
| 互動式 | 引導留言、私訊、點讚 | 拉高互動數據 |
| 夥伴式 | 營造「我們是戰友」感 | 培養粉絲黏性 |
| Slogan | 品牌口號式收尾 | 品牌形象 |
| 反轉式 | 最後翻轉觀眾預期 | 記憶點 |

---

## 選擇指南

依 angle.md 的 `topic` + `sharpness` + `reader_value` 判斷：

- **分享個人經驗** → 03 挑戰類、11 逆襲引流、14 感性觀點
- **表達觀點** → 01 引爆行動、07 PREP、12 金句
- **教學知識** → 04 SCQA、05 三步循環、08 對比、16 教知識經典
- **評論趨勢** → 09 FIRE、02 破案解謎
- **品牌建立** → 10 爆款人設、13 行業揭秘
- **激勵行動** → 06 目標落地、15 通用類

---

## 核心原則

1. 前 3 秒抓住眼球：讓觀眾願意停留
2. 節奏快、資訊集中：短時間內提供衝擊或啟發
3. 結尾誘導行動：呼籲留言、關注、私訊等

---

## Stage 1 Artifact Schema

**檔名**：`drafts/<slug>.framework.md`

**必填 frontmatter 欄位**：

```yaml
stage_entry_announced: true
upstream_gate_passed: true
considered_frameworks:
  - id: "01"
    name: "引爆行動"
    formula: "觀點 → 危害 → 論據 → 結論"
    why_fit: "本題目想改變讀者對 X 的看法，引爆行動的『危害→結論』推進跟 angle 的銳利點對齊"
  - id: "07"
    name: "PREP"
    formula: "Point → Reason → Example → Point"
    why_fit: "..."
  - id: "14"
    name: "感性觀點"
    formula: "事實 → 感受 → 發現問題 → 結論 → 故事 → 總結"
    why_fit: "..."
chosen_framework:
  id: "14"
  name: "感性觀點"
  chosen_reason: "user 說『比較符合我們的場景與情境』；且 angle.md source_quotes 帶感性共鳴元素"
```

**規則**：
- `considered_frameworks` 必須有 **3 個**（不少不多）。少於 3 = reasoning 不足；多於 3 = 未收斂。
- 每個 considered framework 的 `why_fit` 不可為空、不可寫「適合」「OK」「不錯」這類空話。
- `chosen_framework.id` 必須在 16+1 清單（01–16；如有 +1 擴充另議）。**編造視為違規**。
- `chosen_reason` 不可為空、不可寫「順手選」「random」「都可以」。

---

## Plan Failures（含以下任一即 Gate 1→2 FAIL）

- `considered_frameworks` 數量 ≠ 3（少於 3 視為 reasoning 不足；多於 3 視為未收斂）
- 任一 considered framework 的 `why_fit` 為空或寫「適合」「OK」「不錯」這類空話
- `chosen_framework.id` 不在 16+1 清單（編造視為違規）
- `chosen_reason` 為空 或 寫「順手選」「random」「都可以」
- `chosen_framework` 仍為 `?` 或空（user 未選定卻聲稱 Gate PASS）
- `stage_entry_announced` 或 `upstream_gate_passed` frontmatter 欄位缺

---

## Gate 1 → 2 Checklist

進 Stage 2 前，本訊息逐條跑：

- [ ] `drafts/<slug>.framework.md` 存在
- [ ] 列出 **3 個** considered framework
- [ ] 每個 considered framework 的 `why_fit` 非空且不是空話
- [ ] `chosen_framework.id` ∈ 16+1 清單
- [ ] `chosen_reason` 非空（不接受「順手選」）
- [ ] **User align**：「這個框架對嗎」明確發生於本 session

任一未勾 = Gate FAIL = **不得**進 Stage 2。藉口（「差不多」「之後補」）= 違規，重跑 Gate。
