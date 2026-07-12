# Stage 4 — Recording Checklist（本輪 4 部影片）

**用途**：把 `demo-script-*.md` 的佔位符（`<POST_ID>` / `<REPLY_ID>` / draft filename / keyword）一次換成實值，拍攝時照這份逐步對照。
**盤點基準日**：2026-04-23
**帳號**：app owner 帳號（token in `.env`）
**共用規範**：見 `resubmission-plan.md` Stage 4（英文 UI / 英文旁白 / ≤ 2 min / 1080p / 開頭 Architecture Note 3 秒 / 結尾 value card 2 秒）

---

## 全域 Pre-flight（開錄前一次做完）

- [ ] 終端機字體 ≥ 14pt、UTF-8 locale、背景色乾淨（白或深灰都可，不要透明或有壁紙）
- [ ] Browser 視窗登入 `threads.net` 為 app owner 帳號，Activity 分頁可用
- [ ] 關閉無關通知、桌面乾淨
- [ ] 準備好螢幕錄影軟體（OBS / QuickTime / Loom 等）
- [ ] `.env` 有 `THREADS_ACCESS_TOKEN` 且未過期（跑 `threads account info` 驗 token 仍活著，應回 id + username）
- [ ] Architecture Note 字卡（3 秒）預先做好 PNG/MP4 片段，剪輯時合併
- [ ] 4 份影片的結尾 value card（2 秒）也先做好

---

## Video 1 — `content_publish.mp4`

**腳本來源**：`demo-script-content-publish.md`
**實值對照**：

| 腳本佔位符 / 內容                                   | 實值                                                              |
| --------------------------------------------------- | ----------------------------------------------------------------- |
| Step 1-2 單篇貼文內容                               | `Hello from the CLI — demo post for Meta App Review.`          |
| Step 3-4 chain 檔名（原 `drafts/smoke-test.txt`） | **改用 `drafts/app-review-chain.txt`**（英文 3 段，已建） |

**CLI 指令序（實際照抄）**：

```bash
# Step 1: dry-run 單篇
threads post publish "Hello from the CLI — demo post for Meta App Review."

# Step 2: 真發單篇
threads post publish "Hello from the CLI — demo post for Meta App Review." --confirm --yes

# Step 3: dry-run chain
threads post publish-chain drafts/app-review-chain.txt

# Step 4: 真發 chain
threads post publish-chain drafts/app-review-chain.txt --confirm --yes
```

**Threads app 驗證畫面切換點**：

- Step 2 後：切到 Threads app → profile feed → 新貼文在頂部 → highlight 文字匹配
- Step 4 後：切到 Threads app → 點 chain opener → 展開看到 3 篇按序排列

**Post-demo cleanup**（錄完做，不在鏡頭上）：

```bash
# 刪掉 4 則 demo 貼文
threads post delete <STEP2_POST_ID> --confirm --yes
threads post delete <STEP4_POST_ID_1> --confirm --yes
threads post delete <STEP4_POST_ID_2> --confirm --yes
threads post delete <STEP4_POST_ID_3> --confirm --yes
```

（各 `<STEP*_POST_ID*>` 在 CLI 輸出 `[OK] Published as post <id>` / `[OK] Published chain of 3 posts: ...` 時會打印出來。請錄影時記住或截圖。）

---

## Video 2 — `keyword_search.mp4`

**腳本來源**：`demo-script-keyword-search.md`
**實值對照**：

| 腳本佔位符 / 內容 | 實值                                                                          |
| ----------------- | ----------------------------------------------------------------------------- |
| Keyword 選擇      | `API`（英文；實測命中 10 則 owner 貼文 — 符合 advisor use case narrative） |
| 預期命中數        | ≥ 10 matches（2026-04-23 實測）                                              |

**CLI 指令序**：

```bash
# Step 1: 人類模式
threads posts search "API" --limit 10

# Step 2: JSON envelope
threads posts search "API" --limit 10 --json

# Step 3: Help panel

```

**Threads app 驗證畫面切換點**：

- Step 1 後：切到 Threads app → profile → 滑到其中一則命中的貼文（例如 `18106673401892789` 2026-04-02 的 "這個給AI 用的API（應用程式介面）程式"）→ 文字匹配 CLI 輸出

**Post-demo cleanup**：無（純讀取）

---

## Video 3 — `read_replies.mp4`

**腳本來源**：`demo-script-read-replies.md`
**實值對照**：

| 腳本佔位符    | 實值                                                                                                |
| ------------- | --------------------------------------------------------------------------------------------------- |
| `<POST_ID>` | `17952165552108332`（2026-04-02 原文 "我原本想做 Threads 自動回覆..."，已有 10 則真實他人 reply） |
| 預期 reply 數 | 10（2026-04-23 實測；超過腳本預設的 3，demo 用 `--limit 10` 全展開）                              |

**CLI 指令序**：

```bash
# Step 1: 先在 Threads app 展示目標貼文與 reply 數
# （UI only，無 CLI）

# Step 2: 人類模式
threads post replies 17952165552108332 --limit 10

# Step 3: JSON envelope
threads post replies 17952165552108332 --limit 10 --json
```

**Threads app 驗證畫面切換點**：

- Step 1：開啟 `17952165552108332` 在 Threads web，截圖/錄到 reply count
- Step 2 後：split view 或 cut back，每條 CLI 輸出行對應 Threads app 的一則 reply（**展示前 3-4 則即可**；腳本說 3 則，CLI 會印 10 則——旁白可以說 "showing the first three here for clarity, the full list is retrieved in the JSON envelope next"）

**Post-demo cleanup**：無（純讀取）

---

## Video 4 — `manage_replies.mp4`

**腳本來源**：`demo-script-manage-replies.md`
**實值對照**：

| 腳本佔位符                                           | 實值                                                                                                                                                                                                |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `<POST_ID>`（step 2-3 add reply 的 parent）        | `17952165552108332`                                                                                                                                                                               |
| Step 3 新 reply 文字                                 | `Thanks for the feedback — will follow up shortly.`                                                                                                                                              |
| `<EXISTING_REPLY_ID>`（step 4-5 hide/unhide 目標） | `18104390815927731`（author `@azuma01130626` = **owner 自己對自己貼文的舊測試 self-reply，內容是亂碼**；選它做 hide 目標是零倫理負擔——不影響任何 community member；拍完 unhide 即還原） |
| `<NEW_REPLY_ID>`                                   | CLI 輸出中會打印（錄影時截圖或記住）                                                                                                                                                                |

**CLI 指令序**：

```bash
# Step 2: dry-run 加 reply
threads reply add 17952165552108332 "Thanks for the feedback — will follow up shortly."

# Step 3: 真加 reply
threads reply add 17952165552108332 "Thanks for the feedback — will follow up shortly." --confirm --yes

# Step 4: hide（會在 Threads app 看到目標 reply 被隱藏）
threads reply hide 18104390815927731

# Step 5: unhide（還原）
threads reply unhide 18104390815927731
```

**Threads app 驗證畫面切換點**：

- Step 1：開啟 `17952165552108332` → 展示目標 post 並展開 reply 區；其中要能看到那則亂碼 self-reply（`18104390815927731`）
- Step 3 後：Threads app refresh → 新 reply 出現、作者是 owner 本人
- Step 4 後：Threads app refresh → 亂碼 self-reply 被折疊 / 標示 Hidden
- Step 5 後：Threads app refresh → 亂碼 self-reply 恢復正常顯示

**旁白處理提醒**：旁白在介紹 hide 目標時，誠實標明「這是我自己對自己貼文的舊測試 reply（亂碼）」，並補一句「同樣的 hide / unhide 流程也用於 moderate community replies — 這裡為了不影響 community member，選自己的 reply 做示範」。Reviewer 對「用自己 reply 示範 moderation」通常接受度高，因為 intent 清楚且零副作用。

**Post-demo cleanup**（錄完做）：

```bash
# 刪掉 step 3 新加的 reply
threads post delete <NEW_REPLY_ID> --confirm --yes

# 確認 step 5 已執行（上面已還原），無其他清理
```

---

## 剪輯與驗收

- [ ] 每部加開頭 Architecture Note 字卡（3 秒）
- [ ] 每部加結尾 value card（2 秒）
- [ ] 字幕 / tooltip 依各腳本「螢幕字幕與 tooltip 對照表」打上
- [ ] 每部總時長 ≤ 2 min
- [ ] 輸出為 MP4 1080p
- [ ] 檔名：`assets/app-review/content_publish.mp4` / `keyword_search.mp4` / `read_replies.mp4` / `manage_replies.mp4`
- [ ] 拍攝日留存原始錄製檔作為備份

---

## 帶入 Stage 5 的素材

拍完這 4 部，進 Stage 5 送審時需要：

- 4 部定稿影片
- 每個 permission 的 Notes 文案（Architecture Note + use case 一句話 + 指向本腳本 use case 描述）
- `resubmission-plan.md` 第 2 節 Architecture Note 需做最後的文法 / 用詞 review（Stage 5 開始前補上）
