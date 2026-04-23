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

### 1.3 本次重送範圍（2026-04-23 決策）

| 項目 | 決策 | 理由 |
|---|---|---|
| 範圍 | 重送 5 個 permission | 排除 `profile_discovery` |
| 策略 | 一次全送 | 爭取時效，共用 Architecture Note |
| 排除 `profile_discovery` | 本輪不送 | 現有代碼無實際 use case，為 demo 新增功能違反產品邊界原則 |

**本輪重送清單**：
1. `threads_content_publish`
2. `threads_keyword_search`
3. `threads_manage_replies`
4. `threads_read_replies`
5. `threads_manage_mentions`

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

### Stage 2｜每個 permission 的 demo 腳本撰寫 ⏳ 未開始

每份腳本獨立存檔：`docs/app-review/demo-script-{permission}.md`

| Permission | 腳本檔 | 狀態 |
|---|---|---|
| `content_publish` | `demo-script-content-publish.md` | ⏳ 未建 |
| `keyword_search` | `demo-script-keyword-search.md` | ⏳ 未建 |
| `manage_replies` | `demo-script-manage-replies.md` | ⏳ 未建 |
| `read_replies` | `demo-script-read-replies.md` | ⏳ 未建 |
| `manage_mentions` | `demo-script-manage-mentions.md` | ⏳ 未建 |

每份腳本應包含：
1. **Use case 一句話**（英文，與送審 Notes 一致）
2. **Demo 步驟表**：CLI 指令順序 × 期望輸出 × 要切到 Threads client 驗證的畫面
3. **旁白腳本**（英文，逐句）
4. **螢幕字幕與 tooltip 對照表**
5. **事前準備**（要有幾則貼文、幾個回覆、什麼狀態）

### Stage 3｜CLI 補齊 ✅ 已完成

**現況盤點**（2026-04-23）：

| Permission | 需要展示的動作 | 目前 CLI 指令 | 缺口 |
|---|---|---|---|
| `content_publish` | 發文、發串文 | `threads post publish`、`threads post publish-chain` | **無缺** ✅ |
| `keyword_search` | 關鍵字搜尋 | `threads posts search` | **無缺** ✅ |
| `read_replies` | 讀某貼文回覆 | `threads post replies` | **無缺** ✅ |
| `manage_replies` | 新增回覆、隱藏/取消隱藏、調整誰能回覆 | `threads reply add` / `threads reply hide` / `threads reply unhide` | **無缺** ✅ |
| `manage_mentions` | 查 @mentions、顯示回傳內容 | `threads account mentions` | **無缺** ✅ |

**待補工作**：
- [x] 在 `threads_client.py` 新增 `hide_reply(reply_id)` / `unhide_reply(reply_id)` 方法
- [x] 在 `threads_cli/reply.py`（或新建 `replies.py`）新增子命令 `threads reply hide <id>` / `threads reply unhide <id>`
- [x] 在 `threads_client.py` 新增 `list_mentions(since, until, limit)` 方法（對應 `/me/threads_mentions` 端點）
- [x] 在 `threads_cli/account.py`（或新建 `mentions.py`）新增子命令 `threads account mentions`
- [x] 補單元測試 + 手動 smoke（手動 smoke 在 Task 8）

### Stage 4｜錄影 + 剪輯 ⏳ 未開始

**共用規範**（所有影片都套用）：
- 語言：英文 UI + 英文旁白（CLI 若預設中文輸出需加 `--lang en` 或臨時改 locale）
- 格式：MP4、1080p、≤ 2 分鐘/支（Meta 建議）
- 開頭 3 秒畫面：Architecture Note 的第一句話（白底黑字）
- 每個 CLI 指令顯示前加 tooltip 說明該指令意圖
- 每次 API 回應之後切到 Threads app / web 驗證結果（用同一帳號登入）
- 結尾 2 秒畫面：展示 use case value（一句話）

**逐部 checklist**（階段 2 腳本寫完後再展開）：
- [ ] `content_publish.mp4`
- [ ] `keyword_search.mp4`
- [ ] `manage_replies.mp4`
- [ ] `read_replies.mp4`
- [ ] `manage_mentions.mp4`

### Stage 5｜送審 ⏳ 未開始

- [ ] 每個 permission 的 Notes 文案定稿（含 Architecture Note + Use Case 描述）
- [ ] 上傳 5 部影片至 Meta Developer Dashboard
- [ ] 每個 permission 的送審表單勾選與文案貼上
- [ ] Submit

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
