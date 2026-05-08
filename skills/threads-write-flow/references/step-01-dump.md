# Step 01：原始材料輸入（user dump）

**前置哲學**：本 step 遵守 references/00-philosophy.md 的 5 條原則。

## 目標

讓 user 把腦中所有相關材料倒出來、AI 不打斷。

## AI 在乎什麼

- user 的真實表達不被破壞（語氣 / 軟詞 / 場景 / 真實感受）
- AI 不主動詮釋、不主動結構化、不主動評論
- 等 user 自然停下後再進 Step 2

## 為什麼

dump-first 是這套工作流的核心原則。user 一旦被打斷、會失去思考流暢性，後面 step 會在不完整素材上跑。spec ripple #1 訪談原則的前提：先讓 user 有東西可以「校準」。

## 怎麼跑

- AI 開場：「**你想寫的東西、不管成不成形、想到什麼就講什麼。我先聽完、不打斷、之後我再幫你梳理。**」
- user dump 期間 AI 只回應**最小化反應**（譬如「嗯」「好」）── 不解釋、不評論、不問問題
- user 自然停下（明顯結尾、或主動說「就這樣」）→ 進 Step 2

## reference signal（不是 enforce 判死）

AI 開場語**紅旗訊號**（命中後 sense 自審是否真的在打斷 user）：

- 「請先整理 / 請先想清楚」
- 「請給我結構 / 大綱」
- 「我們先確定主題」

## Gate（進 Step 2 前必過）

- [ ] AI 開場語沒命中紅旗訊號（grep + sense 判斷）
- [ ] user dump 過程 AI 沒打斷（沒 surface 結構化問題、沒主動詮釋）
- [ ] user 明確或自然示意 dump 結束
