# Step 08：反模板化檢查

**前置哲學**：本 step 遵守 references/00-philosophy.md 的 5 條原則。

## 目標

最後一道過濾 ── 確保文章不是「完整、正確、順暢但不像 user」。

## AI 在乎什麼

- 這篇是否有**只屬於這次經驗**的具體問題？（如果換另一個 user 也能寫出來、那就是模板化）
- 是否保留 user 真實語氣？
- 是否有誤判、挫敗、轉折或重新理解的痕跡？
- 是否只是漂亮但空泛？
- 是否變成教學文或勵志文？
- 是否過度依賴固定結構？
- 是否讓 user 覺得「這是我想說的話」？

## 為什麼

標準 AI 文的問題不是寫錯，是寫得太正確。Step 8 是專門抓「正確但不像 user」這種 silent failure。

## 怎麼跑

Step 8 以 sense 自審為主、機械掃描只是輔助參考、不是判死規則。語言判斷靠語意 + 上下文，這是模型的強項；單純 grep 命中容易誤判（譬如「你應該」出現在引用對話、或反諷句）。

### 第一步：sense 自審 ── 用具體 3 句 self-prompt

AI 用以下 3 句話回答（必須引用具體句子、不是飄忽 sense check）：

1. 這篇**最像 user 的一句**在哪？引用、給理由
2. 這篇**最像 AI 文的一句**在哪？引用、給理由
3. 這篇**最可能被砍掉的一段**是哪？指出、給理由

回答完依自己的 3 句答覆**給一版修正**（第 1 句很弱 → 加強；第 2 句很 AI → 改寫；第 3 段該砍 → 砍）。

**reference base fallback**（first-time user、AI 沒看過 user 過去發文）：用「user 在 Step 1 dump 時的原話 / 語氣」當 reference base ── 哪一句最像 user 在 Step 1 講的口氣 / 真實感？把 reference 落到本 session 的素材、不依賴 AI 內化的 user 風格 prior。

### 第二步：surface 給 user 對齊（呼應 10.6 訪談原則）

AI 把第一步的 3 句答覆 + 修正後文章 surface 給 user：「**我覺得這篇最像你的是 X、最像 AI 文的是 Y、最可能砍的是 Z；已經修正成這版，你看對嗎？**」

user 用刪除法判斷 AI 的 sense 對 / 不對：

- 全部對 → 採用、進 Step 9 / 結束
- 部分不對 → 討論該段、AI 重寫
- 整個方向都不對 → 回 Step 7 重修

### 第三步：機械掃描（輔助 reference，不判死）

呼叫 `lints/anti-template-grep.sh` 跑 13.1 三條 grep regex（教學語氣字眼 / 勵志公式字眼 / 空泛開頭）。AI 在 sense 自審時可以參考這些 regex 命中作為**訊號**，但**命中只是「需要看上下文判斷」的提示**，不是「命中即不合格」。最終由 sense + user 對齊決定要不要動。

## 底線

如果文章只是完整、正確、順暢，但不像 user，則不合格 ── 不合格時走第一步 sense 自審重寫。

## sense 層

- 「最像 user 的一句」「最像 AI 文的一句」「最可能砍的段」── 全交模型 sense（用具體 3 句 self-prompt 而非飄忽 check）
- 機械 grep 命中的上下文判斷 ── 模型 sense

## Gate（進 Step 9 前必過）

- [ ] 跑了 3 句 self-prompt（每句都引用具體句子、給理由）
- [ ] surface 給 user 對齊（不只 AI 自審）
- [ ] 機械掃描跑了（grep 結果作為訊號、不判死）
- [ ] user 確認「這是我想說的話」（呼應 13.2 ground truth）
