# App Review 重送計畫

**文檔狀態**：SSOT（單一真實來源）
**啟動日**：2026-04-23
**上次更新**：2026-04-23

> 本文檔為 App Review 重送工作的主控文件。每 session 進行都先讀這份、結束都更新這份。進度以 checkbox 表示；決策紀錄只增不改。

---

## 0. 本文檔怎麼用

- **進度追蹤**：每階段的 checkbox 標示完成狀態
- **決策紀錄**：第 1.3 節寫本次重送的範圍決策，未來不改寫只追加
- **腳本與文案**：第 3 / 第 4 節是實際要上傳到 Meta 的文案草稿
- **不在這份管理的**：程式碼變更（在各 PR / commit）、影片檔案（另存 `assets/app-review/`）

---

## 1. 背景

### 1.1 2026-04-01 送審結果（2026-04-22 收到）

| Permission | 結果 | 備註 |
|---|---|---|
| `threads_basic` | ✅ 核准 | - |
| `threads_manage_insights` | ✅ 核准 | - |
| `threads_content_publish` | ❌ 拒絕 | 螢幕錄影不符 |
| `threads_keyword_search` | ❌ 拒絕 | 螢幕錄影不符 |
| `threads_manage_replies` | ❌ 拒絕 | 螢幕錄影不符 |
| `threads_read_replies` | ❌ 拒絕 | 螢幕錄影不符 |
| `threads_manage_mentions` | ❌ 拒絕 | 螢幕錄影不符 |
| `threads_profile_discovery` | ❌ 拒絕 | 螢幕錄影不符 |

### 1.2 拒絕原因共同點

6 個拒絕理由引用相同條文（《開發商政策》第 1.6 條），核心問題是**螢幕錄影沒展示 end-to-end use case**，缺三要素：

1. 完整 Meta 登入流程
2. 用戶授權畫面
3. 該 permission 的實際使用流程

**關鍵線索**（Meta 回饋模板文末）：

> 如果您的應用程式是伺服器對伺服器應用程式，或者，您的應用程式是使用系統工作人員權杖來存取 Meta API，請在下一次的提交內容中註明，讓我們知道無法看見前端的 Meta 登入驗證流程。

這正是本 app 的架構特性，上次送審沒有明確宣告，導致審查員以一般 app 標準判斷「demo 不完整」。

### 1.3 本次重送範圍（2026-04-23 最終決策）

**決策演進**：5 → 4 → **3**（重新聚焦在「實質增益」）

| 項目 | 決策 | 理由 |
|---|---|---|
| 範圍 | 重送 **3 個** permission | 聚焦在 Standard Access 做不到的新能力 |
| 排除 `content_publish` | 本輪不送 | **Standard Access 下 app owner 發自己貼文本來就能做**（`threads post publish` 已在用）；Advanced 核准後增益為 0。硬送 = 用 reviewer 時間換零增益。 |
| 排除 `manage_replies` | 本輪不送 | 同上——自己貼文下的 reply add/hide/unhide 本來就能做；Advanced 增益為 0。 |
| 排除 `manage_mentions` | 本輪不送，延後單送 | `/me/threads_mentions` endpoint 在核准前完全鎖住（實測回 `Tried accessing nonexisting field` / HTTP 500），無法錄 live demo。硬送重蹈「demo 不完整」覆轍。 |
| **加回 `profile_discovery`** | **本輪送** | **真實 use case 浮現**：user 的核心需求是「URL-first 讀他人公開貼文 text 做分析」——oEmbed 實測只回嵌入 widget 無 text；`keyword_search` 需要先有 keyword；唯一乾淨路徑是 profile_discovery（URL → 拆 @user + shortcode → 列 user posts → 匹配 shortcode → 拿 text）。之前排除「代碼無 use case」的判斷錯了，use case 就是這個。 |

**本輪重送清單**（3 個）：
1. `threads_keyword_search` — 解鎖跨帳號 keyword search + 中文搜尋
2. `threads_read_replies` — 解鎖讀取任何公開貼文的 replies
3. `threads_profile_discovery` — 解鎖 URL-first 讀他人公開貼文 text（旗艦 use case）

**延後單送清單**：
- `threads_manage_mentions` — 3 個核准後再送，採用 Architecture-Demo 策略（見 `demo-script-manage-mentions.md` 的 Plan B）

**永不再送**（本輪及未來）：
- `threads_content_publish` / `threads_manage_replies` — Standard Access 已涵蓋，無 Advanced 增益

---

## 2. Architecture Note（共用英文定稿）

**用途**：每個 permission 送審時都放在 Notes 欄位最前面。

```text
[Architecture Note]
This application is a server-to-server CLI tool used for single-account
content analytics and authoring workflow. It authenticates via a long-lived
user access token obtained once by the developer (app owner) — there is no
end-user frontend, no OAuth flow triggered by third parties, and no system
user token.

Per the App Review guidance, we are explicitly noting this so that the
absence of the Meta Login UI in the screen recording is expected and not
a defect of the demonstration. The authenticated user shown in the demo
is the app owner / developer, using the tool on their own Threads account.

All operations demonstrated (publishing, searching, managing replies, reading
mentions) are executed by the CLI as the authenticated developer account.
The screen recording shows: (1) the CLI command, (2) the API response, and
(3) cross-validation in the native Threads client on the same account.
```

**待辦**：
- [ ] 此段英文送審前再過一次文法與用詞
- [ ] 確認是否要補充 privacy policy / data deletion URL（Meta 若要求再加）

---

## 3. 階段計畫

### Stage 1｜規劃對齊 ✅ 已完成
- [x] 決定優先順序（A：一次全送）
- [x] 決定是否納入 `profile_discovery`（Y：排除）
- [x] 起草 Architecture Note

### Stage 2｜每個 permission 的 demo 腳本撰寫 ✅ 已完成

每份腳本獨立存檔：`docs/app-review/demo-script-{permission}.md`

| Permission | 腳本檔 | 狀態 |
|---|---|---|
| `keyword_search` | `demo-script-keyword-search.md` | ✅ 已建（本輪用） |
| `read_replies` | `demo-script-read-replies.md` | ✅ 已建（本輪用） |
| **`profile_discovery`** | **`demo-script-profile-discovery.md`** | **✅ 已建（本輪用，Plan B Architecture-Demo）** |
| `content_publish` | `demo-script-content-publish.md` | 📦 已建但本輪不送（Standard 已涵蓋，無增益） |
| `manage_replies` | `demo-script-manage-replies.md` | 📦 已建但本輪不送（同上） |
| `manage_mentions` | `demo-script-manage-mentions.md` | ⏸️ 延後單送（Plan B：Architecture-Demo） |

每份腳本包含：
1. **Use case 一句話**（英文，與送審 Notes 一致）
2. **Demo 步驟表**：CLI 指令順序 × 期望輸出 × 要切到 Threads client 驗證的畫面
3. **旁白腳本**（英文，逐句）
4. **螢幕字幕與 tooltip 對照表**
5. **事前準備**（要有幾則貼文、幾個回覆、什麼狀態）

### Stage 3｜CLI 補齊 ⏳ 本輪擴增（新增 profile_discovery）

**現況盤點**（2026-04-23 更新）：

| Permission | 需要展示的動作 | 目前 CLI 指令 | 缺口 |
|---|---|---|---|
| `keyword_search` | 關鍵字搜尋 | `threads posts search` | **無缺** ✅ |
| `read_replies` | 讀某貼文回覆 | `threads post replies` | **無缺** ✅ |
| **`profile_discovery`** | **URL → post text（旗艦）+ 列公開貼文** | — | **本 session 實作中** |
| `content_publish` | 發文、發串文 | `threads post publish` / `publish-chain` | **無缺**（本輪不送） |
| `manage_replies` | 新增回覆、hide/unhide | `threads reply add/hide/unhide` | **無缺**（本輪不送） |
| `manage_mentions` | 查 @mentions | `threads account mentions` | **無缺**（延後單送） |

**已完成（Stage 3 上一批）**：
- [x] `hide_reply` / `unhide_reply` API helper + CLI + tests
- [x] `list_mentions` API helper + CLI + tests

**Scope 決策（2026-04-23）**：
- User 真實 use case 是「URL → 讀內文 → 學習」的 reader 工具，不是系統性 scraper
- 本輪只實作 **`lookup` + `posts`** 兩條 CLI，`get`（查 profile 基本資料）不實作
- Endpoint 探針結果（`scripts/probe_profile_discovery.py`）：`ENDPOINT_LOCKED` — `/{username}` 與 `/{username}/threads` 對自己與他人皆回 HTTP 400 `Object ... does not exist, cannot be loaded due to missing permissions`
- 代碼前瞻實作（照 API spec），unit test 全 mock；影片走 Plan B Architecture-Demo + 誠實展示 400 錯誤當 Step 6 素材

**實作清單（本 session）**：
- [ ] `threads_client.py` 新增 `fetch_user_profile(username)` — 內部 helper，未來需要時用
- [ ] `threads_client.py` 新增 `fetch_user_threads(username, limit, cursor)` — 列某 user 公開貼文；`posts` CLI 直用
- [ ] `threads_client.py` 新增 `resolve_post_by_url(url, token)` — URL-first helper：regex 拆 `@username` + shortcode → 呼 `fetch_user_threads` → 匹配 permalink → 回 post dict
- [ ] 新建 `threads_cli/profile.py` Typer sub-app：
  - `threads profile lookup <URL>` — **旗艦指令**（Plan B Step 2 / 6 用）
  - `threads profile posts <username> [--limit N] [--cursor C]` — 列公開貼文（Plan B Step 3 代碼走讀素材）
- [ ] 在 `threads_cli/cli.py` 註冊 `profile_app`
- [ ] 錯誤碼對應（見 `demo-script-profile-discovery.md` 附錄 A）：`UNSUPPORTED_URL` / `PERMISSION_REQUIRED` / `POST_NOT_FOUND` / `API_ERROR`
- [ ] 新建 `tests/test_threads_client_profile.py`（mock）+ `tests/test_cli_profile.py`（human + JSON + 錯誤碼）
- [ ] 跑 full test suite 確認綠
- [ ] 手動 smoke `threads profile --help` / `threads profile lookup --help`（確認指令註冊成功；實際呼叫預期 400）

### Stage 4｜錄影 + 剪輯 ⏳ 未開始

**共用規範**（所有影片都套用）：
- 語言：英文 UI + 英文旁白（CLI 若預設中文輸出需加 `--lang en` 或臨時改 locale）
- 格式：MP4、1080p、≤ 2 分鐘/支（Meta 建議）
- 開頭 3 秒畫面：Architecture Note 的第一句話（白底黑字）
- 每個 CLI 指令顯示前加 tooltip 說明該指令意圖
- 每次 API 回應之後切到 Threads app / web 驗證結果（用同一帳號登入）
- 結尾 2 秒畫面：展示 use case value（一句話）

**逐部 checklist**（本輪 3 部）：
- [x] `keyword_search.mp4` — 錄於 2026-04-23，原檔 `20260423-0854-57.9175595.mp4`
- [x] `read_replies.mp4` — 錄於 2026-04-23，原檔 `20260423-0848-17.2520671.mp4`
- [ ] **`profile_discovery.mp4`** — 下 session 代碼 + 腳本就位後錄
- [ ] ~~`content_publish.mp4`~~（本輪不送，不錄）
- [ ] ~~`manage_replies.mp4`~~（本輪不送，不錄）
- [ ] ~~`manage_mentions.mp4`~~（延後單送，分開錄）

**拍攝前實值對照表**：`docs/app-review/recording-checklist.md`（2026-04-23 產；本輪只剩 profile_discovery 待錄，下 session 補）

### Stage 5｜送審 ⏳ 未開始（本輪等 profile_discovery 就位才送）

**本輪送 3 個 permission（keyword_search / read_replies / profile_discovery）：**
- [ ] 3 個 permission 的 Notes 文案定稿（含 Architecture Note + Use Case 描述）
- [ ] 上傳 3 部影片至 Meta Developer Dashboard
- [ ] 3 個 permission 的送審表單勾選與文案貼上
- [ ] Submit

**次輪單送 `manage_mentions`（3 個核准後）：**
- [ ] 實測 `/me/threads_mentions` 是否仍 locked；若已解鎖改回 live demo
- [ ] 仍 locked 時走 Architecture-Demo Plan B（見 `demo-script-manage-mentions.md`）
- [ ] （可選）送審前開 Meta Developer Support ticket 釐清 permission-locked endpoint 的 demo 要求

### Stage 6｜收尾 ⏳ 未開始

- [ ] 更新 `memory/project_advanced_access.md`（記錄重送日期與範圍）
- [ ] 更新 `memory/project_api_access_constraint.md`（目前只有 `insights` + `basic` 核准）
- [ ] 建立 / 更新 `memory/project_progress_2026MMDD.md`
- [ ] 更新 `memory/MEMORY.md` 索引
- [ ] 寫 `docs/handoffs/session-handoff-{YYYYMMDD}.md`（按 7 欄位格式）
- [ ] 等待 Meta 審查（歷史上 5-10 工作天）

---

## 4. 待決策事項

_（目前無 — 所有 Q 已決議）_

---

## 5. 變更歷史

| 日期 | 變更 |
|---|---|
| 2026-04-23 | 文檔建立。範圍決策：排除 `profile_discovery`，重送 5 個 permission |
| 2026-04-23 | Stage 3 CLI 補齊完成（6 commits in main）。Stage 2 五份 demo 腳本完成。 |
| 2026-04-23 | 實測 `/me/threads_mentions` 回 `nonexisting field` / HTTP 500。重送範圍 5 → 4（排除 `manage_mentions`，延後單送）。mentions 腳本保留，補 Plan B（Architecture-Demo）。 |
| 2026-04-23 | 錄完 `keyword_search.mp4` / `read_replies.mp4` 2 部影片。 |
| 2026-04-23 | 範圍再調：4 → **3**。**排除** `content_publish` / `manage_replies`（Standard Access 已涵蓋，Advanced 增益為 0）；**加回** `profile_discovery`（user 的核心 URL-first use case 浮現；oEmbed 實測只回嵌入 widget 無 text；唯一乾淨路徑是 profile_discovery）。下 session 補 profile_discovery CLI + 腳本 + 影片。 |
| 2026-04-23 | P0 endpoint 探針（`scripts/probe_profile_discovery.py`）verdict = `ENDPOINT_LOCKED`——`/{username}` 對自己與他人皆回 HTTP 400。決議 **Option A**：代碼前瞻寫（mock test）、腳本走 Plan B Architecture-Demo + 誠實揭露 400 錯誤當影片 Step 6 素材。CLI scope 縮為 `lookup` + `posts` 兩條（`get` 不做）——user 真實 use case 是「URL → 讀內文 → 學習」的 reader 工具。 |
| 2026-04-23 | Stage 2 profile_discovery 腳本完成（`docs/app-review/demo-script-profile-discovery.md`，Plan A 未來版 + Plan B 本輪 Architecture-Demo 雙結構）。 |
