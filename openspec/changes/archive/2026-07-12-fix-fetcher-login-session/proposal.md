## Why

Threads 已於 2026 年對匿名訪客一律回登入頁本體（`og:title="Threads • Log in"`、`og:url` 指向首頁），使 `fetch_threads_post.py` 的匿名管道與 og fallback 全數失效——2026-07-12 LINE 收藏搶救 5/5 全敗即因此。門檻已從「客戶端指紋」變成「伺服器端登入 session」，指紋偽裝無解。抓取邏輯（Relay 解析）本身完好，只差帶登入態。現在處理可讓單條抓取恢復自動化，並把手動 claude-in-chrome 救援降為 fallback。

## What Changes

**抓取身分模型**
- From: 每次 `browser.launch(headless=True)` + 匿名 context（`mobile_context_kwargs`，iPhone Safari UA，無 cookie）
- To: `launch_persistent_context` + 專用 profile（repo 外目錄），`--login` 由使用者本人登入一次重用；Chromium 預設一致指紋，棄用行動 UA 偽裝
- Reason: 伺服器端 session 檢查，匿名不再取得內容
- Impact: breaking（改變 R1「匿名鐵律」）；僅影響本 fetcher，vault 端呼叫點另由 Change A 處理

**og fallback 語意**
- From: Relay 失敗降級為匿名 HTTP GET 解析 og，過 author guard 則 exit 3 partial
- To: 匿名 og 只作「登入牆/匿名入口是否恢復」診斷，不再宣稱 partial 內容
- Reason: 登入牆下 og 無內容可取
- Impact: breaking（改變 R3）

**exit code 契約**
- From: 0=完整、3=og partial、2=全失敗、1=URL 壞
- To: 新增 4=auth required/checkpoint；exit 2 既有語意不變；exit 3 保留但實務上登入態不再產生
- Reason: 登入失效需與 schema drift 區分，否則維運誤判
- Impact: non-breaking 擴充（新增碼），既有碼語意保留

**判死規則**
- From: （早期草案）匿名重導=貼文亡
- To: 匿名層只標 `anonymous_inaccessible` 永不 terminal；terminal 需登入態明確不存在
- Reason: 活貼文對匿名訪客也回登入頁，舊規則會誤殺活帖
- Impact: non-breaking（修正邏輯錯誤）

## Capabilities

### New Capabilities
（無）

### Modified Capabilities
- `threads-post-fetching`: R1 匿名指紋 → 登入 persistent profile；R3 og fallback 內容降級 → 診斷用途；R4 exit code 新增 4=auth required。新增登入失效偵測 requirement。

## Impact

- **程式碼**：`scripts/fetch_threads_post.py`——`mobile_context_kwargs()`、`fetch_page()`、`fetch_og_fallback()`、`main()`（argparse ＋ exit code）；新增 `detect_auth_failure()`、`FetchResult` dataclass
- **CLI 介面**：新增 `--login`、`--profile PATH`、`--headless`、`--auth-check-only`；預設由 headless 改 headed
- **測試**：`tests/test_fetch_threads_post.py`——`mobile_context_kwargs` 匿名測試需改寫；新增 auth-failure 偵測、exit 4、profile lock 測試
- **依賴**：Playwright persistent context（既有 playwright 依賴，無新套件）
- **外部**：使用者需一次性 `--login` 建立 profile；帳號風險自主承擔（見 design Risks）
- **下游**：vault 端 line-import／source-capture 呼叫點改接新 CLI 與 exit 4（Change A，另案）
