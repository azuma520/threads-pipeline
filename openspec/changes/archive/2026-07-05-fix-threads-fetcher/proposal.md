# Proposal: fix-threads-fetcher

## Why

匿名 Playwright fetcher（`scripts/fetch_threads_post.py`）因 Threads 端匿名存取政策改變而全面壞損：匿名開貼文 URL 被 302 到 logged-out feed，拿不到 `BarcelonaPostPageDirectQuery` Relay 資料。vault 端 line-import 有 45 條 threads 素材卡住（`failed_transient`），source-capture 存單篇 Threads 同受影響。官方 API 讀不到任意他人公開貼文（keyword_search 限自己、oEmbed 零內文、profile_discovery 待審），此 fetcher 是唯一管道。使用者已定位 Threads 抓取為長期管道，需修復並提升斷供韌性。

## What Changes

**fetch_page 瀏覽器指紋**
- From: 桌面匿名 context（無 UA 覆寫、viewport 1280×2000）→ 被導去 logged-out feed
- To: 行動版 context（iPhone Safari UA、viewport 390×844、`is_mobile=True`）→ 實測可完整取得 Relay 資料（27 posts、A+B 段完整）
- Reason: 2026-07-05 實測證實行動版 UA 不受匿名政策封鎖
- Impact: non-breaking（輸出契約不變）

**新增：相關串文污染防護**
- From: `walk_posts` 收集頁面所有 post 節點，行動版頁面會混入「相關串文」的他人貼文（實測被 classify 標為 A）
- To: 從 URL 取 `main_author`，A 段只保留主文作者的節點
- Reason: 防止下游 post.md 混入無關貼文
- Impact: non-breaking（桌面版時代 A 段本來就只有主文作者）

**新增：og fallback 降級鏈**
- From: 拿不到 Relay 資料 → dump debug HTML、exit 2、全損
- To: 先降級純 HTTP GET（行動 UA）抓 `og:title`/`og:description`，成功則照常寫輸出目錄並標 `partial`（`meta.json` 標 `fetch_mode: "og_fallback"`、`post.md` frontmatter 標 `partial: true`），exit 3；連 og 都拿不到才走既有 exit 2 路徑
- Reason: 長期管道定位下，單管道斷供代價已被本次事故證明；og meta 是 SEO 資產，比 Relay schema 穩定
- Impact: 新增 exit code 3，呼叫端（vault 端 line-import runner）需後續接線辨識 partial——在接線前 exit 3 的行為以 migration note 記錄

## Capabilities

### New Capabilities
- `threads-post-fetching`: 匿名抓取任意公開 Threads 貼文為結構化 markdown 輸出——主管道（行動版 Playwright + Relay 解析）、降級鏈（og fallback）、污染防護、退出碼契約

### Modified Capabilities
（無——本 repo openspec 初建，無既有 spec）

## Impact

- 程式碼：`scripts/fetch_threads_post.py`（fetch_page、新增 og fallback 與作者過濾、exit code）
- 測試：`tests/test_fetch_threads_post.py` 新增 og 解析、作者過濾、exit code 分流案例（含縮減 fixture）
- 外部呼叫端：vault 端 line-import / source-capture——修復後自動受益；partial 狀態辨識屬 vault 端後續小修（本 change 不動 vault）
- 依賴：無新增（og fallback 用 stdlib / 既有依賴）
