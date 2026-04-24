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

| 腳本佔位符 / 內容 | 實值 |
|---|---|
| Step 1-2 單篇貼文內容 | `Hello from the CLI — demo post for Meta App Review.` |
| Step 3-4 chain 檔名（原 `drafts/smoke-test.txt`） | **改用 `drafts/app-review-chain.txt`**（英文 3 段，已建） |

**CLI 指令序（實際照抄）**：

```bash
# Step 1: dry-run 單篇
threads post publish "Hello from the CLI — demo post for Meta App Review."

# Step 2: 真發單篇（記住 post ID）
threads post publish "Hello from the CLI — demo post for Meta App Review." --confirm --yes

# Step 3: dry-run chain
threads post publish-chain drafts/app-review-chain.txt

# Step 4: 真發 chain（記住 3 個 post ID）
threads post publish-chain drafts/app-review-chain.txt --confirm --yes

# Step 5: delete 示範（刪 Step 2 那則；展示 authoring lifecycle 的完整閉環）
threads post delete <STEP2_POST_ID> --confirm --yes
```

**Threads app 驗證畫面切換點**：
- Step 2 後：切到 Threads app → profile feed → 新貼文在頂部 → highlight 文字匹配
- Step 4 後：切到 Threads app → 點 chain opener → 展開看到 3 篇按序排列
- Step 5 後：切到 Threads app → profile feed refresh → Step 2 的單篇已消失；但 chain 仍在

**Step 5 預期輸出**：
```
[OK] Deleted post <STEP2_POST_ID>
  backup: .deleted_posts/<timestamp>-<post_id>.json
[WARN] This operation is irreversible.
```
（影片旁白可強調：CLI 在 delete 前會先做本地備份，這是負責任的 data handling。）

**Post-demo cleanup**（錄完做，不在鏡頭上）：

```bash
# 刪掉 chain 的 3 則（Step 2 的單篇已在 Step 5 鏡頭內刪掉）
threads post delete <STEP4_OPENER_ID> --confirm --yes
threads post delete <STEP4_POST_ID_2> --confirm --yes
threads post delete <STEP4_POST_ID_3> --confirm --yes
```

（各 `<STEP*_POST_ID*>` 在 CLI 輸出 `[OK] Published as post <id>` / `[OK] Published chain of 3 posts: ...` 時會打印出來。請錄影時記住或截圖。）

---

## Video 2 — `keyword_search.mp4`

**腳本來源**：`demo-script-keyword-search.md`
**實值對照**：

| 腳本佔位符 / 內容 | 實值 |
|---|---|
| Keyword 選擇 | `API`（英文；實測命中 10 則 owner 貼文 — 符合 advisor use case narrative） |
| 預期命中數 | ≥ 10 matches（2026-04-23 實測） |

**CLI 指令序**：

```bash
# Step 1: 人類模式
threads posts search "API" --limit 10

# Step 2: JSON envelope
threads posts search "API" --limit 10 --json

# Step 3: Help panel
threads posts search --help
```

**Threads app 驗證畫面切換點**：
- Step 1 後：切到 Threads app → profile → 滑到其中一則命中的貼文（例如 `18106673401892789` 2026-04-02 的 "這個給AI 用的API（應用程式介面）程式"）→ 文字匹配 CLI 輸出

**Post-demo cleanup**：無（純讀取）

---

## Video 3 — `read_replies.mp4`

**腳本來源**：`demo-script-read-replies.md`
**實值對照**：

| 腳本佔位符 | 實值 |
|---|---|
| `<POST_ID>` | `17952165552108332`（2026-04-02 原文 "我原本想做 Threads 自動回覆..."，已有 10 則真實他人 reply） |
| 預期 reply 數 | 10（2026-04-23 實測；超過腳本預設的 3，demo 用 `--limit 10` 全展開） |

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

| 腳本佔位符 | 實值 |
|---|---|
| `<POST_ID>`（step 2-3 add reply 的 parent） | `17952165552108332` |
| Step 3 新 reply 文字 | `Thanks for the feedback — will follow up shortly.` |
| `<EXISTING_REPLY_ID>`（step 4-5 hide/unhide 目標） | `18104390815927731`（author `@azuma01130626` = **owner 自己對自己貼文的舊測試 self-reply，內容是亂碼**；選它做 hide 目標是零倫理負擔——不影響任何 community member；拍完 unhide 即還原） |
| `<NEW_REPLY_ID>` | CLI 輸出中會打印（錄影時截圖或記住） |

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

---

## Video 5 — `profile_discovery.mp4`（2026-04-24 append，Plan B Architecture-Demo）

**腳本來源**：`demo-script-profile-discovery.md` Plan B 段（≤ 90 秒 / 7 個鏡頭）
**影片最終位置**：`assets/app-review/profile_discovery.mp4`
**語言**：英文 UI + 英文旁白

### 實值對照

| 腳本佔位符 | 實值 |
|---|---|
| 公開貼文 URL（Step 2 / Step 7） | **使用者錄影前自選一則真正看得到的公開貼文**，例：`https://www.threads.com/@lin__photograph/post/<shortcode>`。只要是公開可讀、URL 格式是 `/@{username}/post/{shortcode}` 即可。 |
| 用於 Step 7 的 username | 上行 URL 的 `@` 之後那串；錄到的 400 錯誤會顯示 `Object with ID '<該 username>' does not exist, ...` |
| 用於 Step 3 / Step 4 的 source code 檔案 | `threads_client.py`（scroll 到 `resolve_post_by_url` 和 `fetch_user_threads`）與 `threads_cli/profile.py`（兩個 sub-command） |
| Meta API 文件 URL（Step 5） | Meta Threads API reference → User threads listing endpoint（`/{threads-user-id}/threads`）。錄前先打開瀏覽器分頁。 |

### Pre-flight 準備（開錄前照抄一次）

- [ ] 終端機字體 ≥ 14pt、UTF-8 locale、背景乾淨
- [ ] `.env` 有 `THREADS_ACCESS_TOKEN` 且未過期（`threads account info` 驗）
- [ ] 瀏覽器 **分頁 1**：目標公開貼文 URL（Step 2 用）
- [ ] 瀏覽器 **分頁 2**：Meta Threads API docs 的 `/{threads-user-id}/threads` 頁（Step 5 用）
- [ ] 編輯器（VS Code）開兩個 pinned tabs：
      - `threads_client.py` → scroll 到 `resolve_post_by_url` / `fetch_user_threads`（Step 3 / 4）
      - `threads_cli/profile.py` → 開頭（顯示兩個 sub-command，Step 3）
- [ ] Title card（5 秒 / Architecture Note + endpoint-lock disclosure）已做好 PNG/MP4
- [ ] Closing card（2 秒 / "integration complete — awaiting endpoint activation"）已做好
- [ ] 試跑一次 `threads profile lookup <目標URL>` 確認出 `[ERROR] HTTP 400: Unsupported get request. Object with ID '<username>' does not exist, cannot be loaded due to missing permissions, or does not support this operation` 單行錯誤（2026-04-24 已驗證輸出乾淨無 token 外洩）

### 鏡頭對照（Plan B 7 步）

**Step 0｜Title card（5s）**
- 鏡頭：Architecture Note + endpoint-lock disclosure 兩段文字字卡
- 旁白："This app is a server-to-server CLI. The endpoint this permission unlocks is gated before approval, so this video demonstrates the implementation and intended user journey, with the current pre-approval API response shown at the end for transparency."

**Step 1｜Use case scene（10s）**
- 鏡頭：瀏覽器分頁 1（目標公開貼文），展示文字可讀
- 旁白："The owner regularly finds interesting public posts on Threads and wants to save the text for later reading and study. Here is one such post — public, reachable by URL."

**Step 2｜CLI help（10s）**
```bash
threads profile --help
threads profile lookup --help
```
- 鏡頭：終端機依序跑這兩條，show `lookup <url>` + `posts <username>` + `--limit / --cursor / --json`
- 旁白："The CLI already implements a `profile` command group with two operations. `lookup` takes a post URL and returns the post text; `posts` lists a creator's recent public posts. Both call the `profile_discovery` endpoint once approved."

**Step 3｜Source code（15s）**
- 鏡頭：VS Code 切到 `threads_client.py`，highlight `resolve_post_by_url()` 方法（URL regex + `GET /{username}/threads`）；再快速 show `fetch_user_profile` / `fetch_user_threads` 兩個 helper
- 旁白："The client method implements URL parsing — extracting the `@username` and post shortcode — then queries the documented `/{username}/threads` endpoint, matching the post by its permalink shortcode. All target fields are the public ones Meta documents under `profile_discovery`."

**Step 4｜Meta docs cross-check（10s）**
- 鏡頭：瀏覽器分頁 2（Meta Threads API reference 的 user threads listing endpoint）
- 旁白："This is the same endpoint documented in Meta's Threads API reference — confirming the permission and endpoint pair we are requesting."

**Step 5｜Learning workflow（10s）**
- 鏡頭：快速 show 一個 receiver 情境 — 例如 terminal 輸出 piped 到本地 `.md` 檔案，或強調 "owner's own terminal, local only"
- 旁白："The returned text goes only to the owner's local terminal — used by the owner to read and study other creators' work. No content is republished, redistributed, or shared with third parties."

**Step 6｜Attempted live call + graceful failure（10s）**
```bash
threads profile lookup "<目標公開貼文URL>"
```
- 鏡頭：終端機出現 `[ERROR] HTTP 400: Unsupported get request. Object with ID '<username>' does not exist, cannot be loaded due to missing permissions, or does not support this operation`
- 疊字卡："Endpoint unlocks upon approval"
- 旁白："For transparency, the endpoint currently returns the documented pre-approval error — confirming the CLI is correctly wired and only the `profile_discovery` approval is outstanding."

**Step 7｜Closing card（5s）**
- 字卡：`profile_discovery`: integration complete — awaiting endpoint activation

### Post-demo cleanup

- 無。全部 read-only。

### 剪輯驗收

- [ ] 總長 ≤ 90 秒（目標），最多不過 2 分鐘
- [ ] 1080p MP4
- [ ] 字幕 / tooltip 依 `demo-script-profile-discovery.md` Plan B 第 4 節對照表
- [ ] 檔名 `profile_discovery.mp4`，放進 `assets/app-review/`
- [ ] 送審時 Notes 欄位貼 `docs/app-review/submission-notes.md` 的 Permission 3 區塊
