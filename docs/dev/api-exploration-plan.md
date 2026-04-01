# Threads API 功能邊界探索計畫

目標：系統性測試 keyword_search 的所有參數組合，摸清能做什麼、不能做什麼，為後續功能設計提供事實依據。

## 已確認可用的 endpoint

- `keyword_search` — 關鍵字搜尋公開貼文
- `me/threads` — 自己的貼文列表
- `{post_id}/insights` — 單篇貼文 insights
- `me/threads_insights` — 帳號層級 insights

## 已確認不可用的 endpoint

- `threads_profile/{user_id}` — 400 錯誤，需額外權限
- `public_profiles/{user_id}/threads` — endpoint 不存在

---

## 測試項目

### 1. search_type 比較

| 測試 | 參數 | 要觀察的 |
|------|------|----------|
| 1a | `search_type=TOP` | 回傳順序、是否固定 |
| 1b | `search_type=RECENT` | 回傳順序、時間分布 |
| 1c | 同關鍵字兩種 type 比較 | 結果重疊度多高 |

### 2. search_mode 比較

| 測試 | 參數 | 要觀察的 |
|------|------|----------|
| 2a | `search_mode=KEYWORD`（預設） | 基準線 |
| 2b | `search_mode=TAG` | 結果有什麼不同、是否需要 # 符號 |
| 2c | TAG 模式搜中文標籤 | 中文 tag 能不能用 |

### 3. author_username 篩選

| 測試 | 參數 | 要觀察的 |
|------|------|----------|
| 3a | 搜自己（azuma01130626） | 確認能搜到自己的貼文 |
| 3b | 搜知名帳號 | 能不能搜到別人的貼文 |
| 3c | 不存在的 username | 回傳空還是錯誤 |
| 3d | author_username + 無關關鍵字 | q 和 author 是 AND 還是 OR |

### 4. media_type 篩選

| 測試 | 參數 | 要觀察的 |
|------|------|----------|
| 4a | `media_type=TEXT` | 只回文字貼文 |
| 4b | `media_type=IMAGE` | 只回有圖片的 |
| 4c | `media_type=VIDEO` | 只回有影片的 |
| 4d | 不帶 media_type | 預設行為是什麼 |

### 5. limit 和分頁

| 測試 | 參數 | 要觀察的 |
|------|------|----------|
| 5a | `limit=1` | 最小值 |
| 5b | `limit=100` | 文件說的最大值 |
| 5c | `limit=101` | 超過最大值會怎樣 |
| 5d | 用 paging cursor 翻頁 | 能翻幾頁、總共能拿到多少筆 |

### 6. since / until 時間範圍

| 測試 | 參數 | 要觀察的 |
|------|------|----------|
| 6a | 過去 24 小時 | 基準線 |
| 6b | 過去 7 天 | 結果量差異 |
| 6c | 過去 30 天 | 有沒有上限 |
| 6d | 不帶 since/until | 預設搜多遠 |

### 7. fields 可回傳欄位

| 測試 | 參數 | 要觀察的 |
|------|------|----------|
| 7a | 基本欄位 `id,text,username,timestamp` | 基準線 |
| 7b | 加 `has_replies,is_quote_post,is_reply` | 互動相關 |
| 7c | 加 `media_type,media_url,thumbnail_url` | 媒體相關 |
| 7d | 加 `topic_tag` | 能不能拿到貼文的 tag |
| 7e | 加 `link_attachment_url` | 連結附件 |
| 7f | 加 `poll_attachment` | 投票 |
| 7g | 加 `like_count` | 搜別人的貼文能不能拿到按讚數 |
| 7h | 全部欄位一起要 | 哪些會回、哪些不會 |

### 8. Rate Limit 觀察

| 測試 | 方法 | 要觀察的 |
|------|------|----------|
| 8a | 連續快速送 10 個請求 | 有沒有被限速 |
| 8b | 記錄 response header | 有沒有 rate limit 相關的 header |

### 9. 搜尋品質

| 測試 | 方法 | 要觀察的 |
|------|------|----------|
| 9a | 搜中文關鍵字（「人工智慧」） | 中文搜尋品質 |
| 9b | 搜多字詞（「AI Agent 自動化」） | 是 AND 還是 OR |
| 9c | 搜特殊字元 | 怎麼處理 |

---

## 產出

跑完所有測試後，整理成一份 `api-exploration-results.md`，記錄：
- 每個參數的實際行為
- 功能邊界（能做/不能做）
- Rate limit 實測數據
- 對後續功能設計的影響
