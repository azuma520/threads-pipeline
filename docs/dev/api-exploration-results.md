# Threads API 功能邊界探索結果

> 測試時間：2026-04-01 10:06 Asia/Taipei  
> 測試帳號：azuma01130626 (ID: 34782204798093277)  
> 原始數據：[api-exploration-raw.json](api-exploration-raw.json)

---

## 摘要

| 類別 | 通過 | 失敗 | 重要發現 |
|------|------|------|----------|
| search_type | 2/2 | 0 | TOP 和 RECENT 結果高度重疊 |
| search_mode | 2/3 | 0 | TAG 模式中文搜不到 |
| author_username | 4/4 | 0 | **參數被完全忽略** |
| media_type | 2/3 | 1 | 正確值是 `TEXT` 不是 `TEXT_POST`；`IMAGE` 可用 |
| limit/分頁 | 4/4 | 0 | **實際最大 limit = 50**（非文件說的 100）；分頁可用 |
| since/until | 4/4 | 0 | 時間篩選正常 |
| fields | 8/8 | 0 | **大量欄位被靜默忽略**（like_count、topic_tag 等） |
| Rate Limit | 2/2 | 0 | 10 次快速請求無限速、無 rate limit headers |
| 搜尋品質 | 3/3 | 0 | **中文搜尋/多字詞搜尋結果為空** |

---

## 1. search_type 比較

| 測試 | 結果 | 說明 |
|------|------|------|
| 1a: TOP | ✅ 10 筆 | 回傳按「熱門度」排序 |
| 1b: RECENT | ✅ 10 筆 | 回傳按「時間」排序 |
| 1c: 重疊度 | — | 樣本 3 篇中 3 篇重疊（100%） |

**結論：** TOP 和 RECENT 在小樣本下差異不大。`search_type` 參數有效，但「AI」這種熱門關鍵字的 TOP 和 RECENT 結果高度重疊。差異可能在更大量的結果中才明顯。

---

## 2. search_mode 比較

| 測試 | 結果 | 說明 |
|------|------|------|
| 2a: KEYWORD | ✅ 10 筆 | 全文搜尋，正常 |
| 2b: TAG (英文) | ✅ 10 筆 | 搜 `#AI` tag，正常 |
| 2c: TAG (中文) | ✅ 0 筆 | 中文 tag 搜不到東西 |

**結論：**
- `KEYWORD` 搜全文，`TAG` 搜 hashtag，不需要加 `#` 符號
- **中文 tag 完全不可用**（回傳 0 筆）
- TAG 模式只適合英文 tag

---

## 3. author_username 篩選

| 測試 | 結果 | 回傳 username | 說明 |
|------|------|---------------|------|
| 3a: 自己 | ✅ 10 筆 | azuma01130626 | — |
| 3b: zaborsky | ✅ 10 筆 | azuma01130626 | ⚠ 回傳的不是 zaborsky 的貼文！ |
| 3c: 不存在帳號 | ✅ 10 筆 | azuma01130626 | ⚠ 不存在的帳號也回傳結果 |
| 3d: 自己 + 無關關鍵字 | ✅ 0 筆 | — | q 和 author 是 AND 邏輯 |

**結論：**
- **`author_username` 參數被 API 完全忽略**
- 無論傳什麼 username，回傳結果都相同
- 3a/3b/3c 回傳的都是相同的貼文（都是 azuma01130626 的）
- 3d 回傳 0 筆是因為關鍵字「量子力學微積分」沒有匹配，不是 author 篩選的效果
- **無法用 API 篩選特定作者的貼文**

---

## 4. media_type 篩選

| 測試 | 結果 | 說明 |
|------|------|------|
| 4a: TEXT_POST | ❌ 500 | 錯誤值，正確應為 `TEXT` |
| 4b: IMAGE | ✅ 1 筆 | 正常 |
| 4c: VIDEO | ✅ 0 筆 | 正常（只是沒有匹配的影片） |
| 4d: 不帶 | ✅ 10 筆 | 預設回傳所有類型 |

**結論：**
- 有效的 media_type 值：`IMAGE`、`TEXT`、`VIDEO`
- 注意是 `TEXT` 不是 `TEXT_POST`（跟 Threads API 其他地方的命名不一致）
- 不帶 media_type 預設回傳所有類型
- 錯誤訊息清楚：`"Param media_type must be one of {IMAGE, TEXT, VIDEO}"`

---

## 5. limit 和分頁

| 測試 | 結果 | 說明 |
|------|------|------|
| 5a: limit=1 | ✅ 1 筆 | 最小值正常 |
| 5b: limit=100 | ✅ 50 筆 | **實際最大 = 50，不是文件說的 100** |
| 5c: limit=101 | ✅ 50 筆 | 超過上限自動降至 50，不報錯 |
| 5d: 分頁 | ✅ 5 頁 125 筆 | 分頁正常運作 |

**結論：**
- **實際 limit 上限是 50**（不是 API 文件說的 100）
- 超過 50 會被靜默截斷，不會報錯
- 分頁透過 `paging.cursors.after` 正常運作
- 5 頁共取得 125 篇（25 x 5），每頁穩定
- 分頁可以一直翻（未測到底）

---

## 6. since / until 時間範圍

| 測試 | 結果 | 說明 |
|------|------|------|
| 6a: 24h | ✅ 25 筆 | — |
| 6b: 7 天 | ✅ 25 筆 | — |
| 6c: 30 天 | ✅ 25 筆 | — |
| 6d: 不帶 | ✅ 25 筆 | — |

**結論：**
- `since` / `until` 接受 Unix timestamp
- 時間篩選正常，但因為都限制了 limit=25，結果數相同
- 不帶 since/until 時預設搜尋範圍不明（回傳的貼文時間跨度待進一步觀察）
- 目前 pipeline 用 1 天範圍已足夠

---

## 7. fields 可回傳欄位

| 測試 | 要求的欄位 | 實際回傳 | 說明 |
|------|-----------|---------|------|
| 7a: 基本 | id,text,username,timestamp | ✅ 全部 | 基礎欄位都有 |
| 7b: 互動 | +has_replies,is_quote_post,is_reply | ✅ 全部 | 互動狀態欄位可用 |
| 7c: 媒體 | +media_type,media_url,thumbnail_url | ⚠ 只有 media_type | media_url、thumbnail_url 被忽略 |
| 7d: topic_tag | +topic_tag | ❌ 被忽略 | 不回傳 |
| 7e: link_attachment_url | +link_attachment_url | ❌ 被忽略 | 不回傳 |
| 7f: poll_attachment | +poll_attachment | ❌ 被忽略 | 不回傳 |
| 7g: like_count | +like_count | ❌ 被忽略 | **搜尋結果不回傳按讚數** |
| 7h: 全部 | 所有欄位 | 9 個欄位 | 見下方清單 |

**keyword_search 實際可用欄位（7h 測試結果）：**

```
✅ id, text, username, timestamp
✅ has_replies, is_quote_post, is_reply
✅ media_type, permalink

❌ like_count — 靜默忽略
❌ media_url — 靜默忽略
❌ thumbnail_url — 靜默忽略
❌ topic_tag — 靜默忽略
❌ link_attachment_url — 靜默忽略
❌ poll_attachment — 靜默忽略
```

**結論：**
- **keyword_search 回傳的欄位非常有限**
- 最關鍵的缺失：**沒有 like_count**（無法直接判斷貼文熱度）
- media_url 不可用（無法直接取得圖片/影片連結）
- topic_tag 不可用（無法知道貼文的 hashtag）
- 不支援的欄位不會報錯，而是靜默忽略

---

## 8. Rate Limit 觀察

| 測試 | 結果 | 說明 |
|------|------|------|
| 8a: 連續 10 次 | ✅ 全部 200 | 無限速 |
| 8b: Headers | — | 無 rate limit 相關 header |

**結論：**
- 10 次快速連續請求未被限速
- Response headers 中沒有標準的 rate limit 欄位（X-RateLimit-* 等）
- 有 `x-fb-request-id` 和 `x-fb-trace-id`（Facebook 內部 tracing）
- **注意：** 10 次可能還不夠觸發限速，更大量的測試需小心

---

## 9. 搜尋品質

| 測試 | 結果 | 說明 |
|------|------|------|
| 9a: 「人工智慧」 | ✅ 0 筆 | 中文搜尋無結果 |
| 9b: 「AI Agent 自動化」 | ✅ 0 筆 | 多字詞搜尋無結果 |
| 9c: 「C++ #coding」 | ✅ 0 筆 | 特殊字元搜尋無結果 |

**結論：**
- **中文關鍵字搜尋幾乎無用**（繁體中文「人工智慧」回傳 0 筆）
- 多字詞搜尋（含空格的多詞組合）結果為空
- 特殊字元可能干擾搜尋
- **keyword_search 本質上只適合搜尋簡單的英文關鍵字**
- 目前 pipeline 用「AI」「LLM」「Claude」等英文關鍵字是正確策略

---

## 對 Pipeline 的影響

### 立即可優化

1. **修正 limit 設定：** 目前 config `max_posts_per_keyword: 25` 已經合理，但知道實際上限是 50 而非 100
2. **修正 media_type 值：** 如果要用 media_type 篩選，正確值是 `TEXT` 而非 `TEXT_POST`
3. **加入分頁：** 如果想要更多結果，可以實作分頁取得更多貼文（目前只取第一頁）

### 功能限制需注意

1. **無法篩選特定作者** — `author_username` 參數無效
2. **搜尋結果沒有 like_count** — 無法用 keyword_search 直接判斷貼文熱度
3. **中文搜尋不可用** — 只能用英文關鍵字
4. **可用欄位有限** — 沒有 media_url、topic_tag、link_attachment_url

### 對 V2.5+ 規劃的影響

- **共鳴度分析：** 無法從 keyword_search 取得 like_count，需要透過其他方式（如 `{post_id}/insights`）來取得互動數據
- **議題分析：** 無法取得 topic_tag，分類需完全依賴 AI 分析貼文內容
- **作者追蹤：** 無法用 API 篩選特定作者，需要搜集後再本地過濾
- **中文趨勢：** 純中文關鍵字搜不到東西，建議關鍵字策略以英文為主，搭配簡短的技術術語

---

## 附錄：Response 速度統計

| 操作 | 平均回應時間 |
|------|-------------|
| keyword_search | ~600-800ms |
| 帶篩選條件 | ~500-700ms |
| 單筆 limit=1 | ~520ms |

API 回應速度穩定，無明顯效能問題。
