<!--
Raw capture of superpowers:brainstorming output.
本檔原樣捕捉 brainstorming skill 的產出（決策紀錄格式），不強制結構。
design.md 從本檔萃取並重新整理為結構化設計文件。
-->

# Brainstorm: fix-threads-fetcher

日期：2026-07-05
參與：あずま（決策）+ Claude（脈絡調查、實測、提案）

## 背景

`scripts/fetch_threads_post.py`（匿名 Playwright fetcher）於 2026-07-05 確診壞損：
匿名開 Threads 貼文 URL 被 302 到 logged-out 首頁 feed（dump 顯示
`BarcelonaLoggedOutFeedContainerQuery` ×8、無 `BarcelonaPostPageDirectQuery`、
零登入表單標記），屬 Threads 端匿名存取政策改變，**非限流**（兩輪 runner 隔
40 分鐘同樣前 5 條全 Timeout）。

影響面：
- vault 端 line-import 有 45 條 threads pending（`failed_transient`）卡住
- source-capture 存單篇 Threads 走同一支 fetcher，同受影響
- repo 內部無生產呼叫者（main pipeline 走官方 API，與 fetcher 無耦合）

## 脈絡調查結論（Explore agent + 直接確認）

1. **fetcher 現況**：純匿名 Playwright（headless chromium、無 UA 覆寫、無
   storage_state），`new_context(viewport 1280×2000)`，靠頁面
   `<script data-sjs type="application/json">` 裡含 `BarcelonaPostPageDirectQuery`
   的 Relay JSON 解析。解析層（`extract_relay_json`/`walk_posts`/`classify`/
   `filter_by_flags`/`render_markdown`）有完整單測；網路層（`fetch_page`）零測試。
2. **官方 API 讀不到任意他人公開貼文**（硬約束）：keyword_search Standard
   Access 只搜自己貼文；oEmbed 於 2026-04-23 實測只回 embed widget、零內文
   （`docs/handoffs/session-handoff-20260423.md:387-389`）；profile_discovery 需
   Advanced Access，App Review 未過。這是匿名爬蟲存在的理由。
3. **輸出契約**：`drafts/library/{date}_{author}_{code}/` 四檔
   （post.md / meta.json / relay.json / screenshot.png），drift 時 dump HTML 到
   `_debug/` 並 exit 2。

## 當場實測（2026-07-05，樣本：threads.net/@lingyu9683/post/DISnS0JJywN）

| 支線 | 結果 |
|------|------|
| 桌面匿名 Playwright（現況） | ❌ logged-out feed（既有確診） |
| oEmbed | ❌ 已死（repo 內 2026-04-23 實測，零內文） |
| 純 curl 桌面 UA | ❌ 空殼頁（200 但無 Relay、無 og） |
| 純 curl 行動 UA（iPhone Safari） | ⚠️ 無 Relay payload（marker 命中僅為模組清單假陽性），**但有 og:title + og:description（實際內文，~151 字，疑似截斷上限、無 B 段）** |
| **Playwright + 行動 UA + is_mobile** | ✅ **無 logged-out 導向，`extract_relay_json` 成功，`walk_posts` 抽出 27 posts，A（主文）+ B（作者自串）內文完整，現有解析器直接可用** |

附帶發現：行動版頁面載入「相關串文」，其他作者的頂層貼文會被 `walk_posts`
收進來且 classify 標為 A → 需作者過濾防護（新風險，桌面版時代無此問題或未爆）。

## 擴大實測（使用者質疑「確定能解決問題嗎」後補做，2026-07-05）

從 `7、專案/LINE收藏搶救/state.json` 抽 7 條真實 pending URL（7 個不同作者），
套行動版 context 序列跑（間隔 7 秒）：

| 作者 | 節點 | A主文 | A_foreign | B自串 | logged-out |
|------|-----:|------|----------:|------:|-----------:|
| lightpdf_tw | 19 | ✅80字 | 0 | 0 | 0 |
| prompt_case | 22 | ✅231字 | 0 | 0 | 0 |
| gucci_dgixoption | 6 | ✅366字 | 0 | 1 | 0 |
| jet.sun999 | 1 | ✅99字 | 0 | 0 | 0 |
| keantares | 16 | ✅174字 | 0 | 1 | 0 |
| dseditor | 1 | ✅151字 | 0 | 0 | 0 |
| huanwangorg | 1 | ✅115字 | 0 | 0 | 0 |

**主管道 7/7 成功（連首樣本 = 8/8）**，跨單則到 22 節點長串、有無自串皆涵蓋，
零 logged-out、零風控。結論修正：(1) n=1→n=8 實證，核心修法穩；(2) 相關串文
污染是**偶發**（僅首樣本觸發），防護保留但非常態；(3) og fallback 本批未觸發，
仍 n=0（保險絲路徑）。gucci 那條完整 post.md 已抓給使用者確認品質（A 366 字
無截斷 + B 段 YouTube 連結正確接上）。

## Codex（gpt-5.5）設計審查採納（2026-07-05）

經 `llm-reviewer` 取第三方審查，採納 7 條：① og fallback 加 author guard
（`og:title` 須含 `(@author)`，否則 exit 2，防降級鏈掩蓋主管道壞損——最重要）、
② exit code SHALL 措辭改為 fetcher 端可保證、③ 同作者非本串邊界列 apply 判斷、
④ 指紋契約抽 `mobile_context_kwargs` 純函式使可測、⑤ og 正則放寬屬性順序、
⑥⑦ design/spec 措辭一致化。詳見 design.md D2/D5/D7 與 plan Self-Review 落點表。

## 決策鏈

### Q1：需求定位——長期管道還是一次性搶救？
**決策：長期管道。** 之後 LINE 收藏、source-capture 都會持續存 Threads 貼文，
fetcher 要修到可長期維運，值得投資較穩方案。

### Q2：若走登入態（路線 a），掛誰的帳號？
**決策：盡量不用登入態。** 先驗證匿名支線；登入態只當最後手段（官方 API token
綁使用者真帳號，爬蟲若帶同帳號 cookie 被風控，發文管道陪葬）。若匿名全死再
回來選帳號（屆時傾向開小帳隔離）。

### Q3：修復方案拾取（三案）
- 方案 1 最小修：只改 fetch_page 行動版 context + 作者過濾。
- **方案 2（採納）：方案 1 + 降級鏈**——主管道失敗時降級 curl 行動 UA 抓
  og:description，存為標記 partial 的摘要結果；再失敗才 terminal。配合既有
  `_debug` drift dump。
- 方案 3：方案 1 + 純監控，不做降級。

**決策：方案 2。** 理由：長期管道定位下，本次事故已證明單管道斷供代價
（45 條卡一週）；og 降級實作成本低（純 HTTP + meta 正則），og meta 是 SEO
資產、比 Relay schema 穩定；「指針可爛、貨不能丟」——partial 摘要好過全損。

## 批准的設計（六節，2026-07-05 使用者批准）

**§1 主管道修復（fetch_page）**：`new_context()` 加 `user_agent=MOBILE_UA`
（模組層常數，iPhone Safari 字串）、`viewport 390×844`、`is_mobile=True`。
導航策略（networkidle、30s timeout）與單次 launch/close 生命週期不變。
解析層零改動。

**§2 相關串文污染防護**：從 URL 取 `main_author`，A 段只保留
`username == main_author` 的節點；B/C 段本來就綁作者語意，D 段維持既有邏輯。
實作時先驗證 classify 對他人頂層貼文的實際行為，防護加在正確的層。

**§3 降級鏈（og fallback）**：主管道拿不到 Relay 時，降級純 HTTP GET
（行動 UA，不開 browser）→ 解析 og:title + og:description → 照常寫輸出目錄，
`meta.json` 標 `fetch_mode: "og_fallback"`、`post.md` frontmatter 標
`partial: true`。退出碼：`0` 完整成功、`3` partial 成功（新增）、`2` 連 og
都拿不到（維持既有 drift dump 行為）。

**§4 呼叫端接線（scope 邊界）**：本 change 編輯範圍 = threads-pipeline repo。
vault 端 line-import runner 認識 exit 3 / partial 狀態屬 vault 端後續小修，
記為 migration note。45 條 pending 都是 failed_transient，fetcher 修好後
`runner.py --batch threads` 自動重試補跑。

**§5 測試**：解析層既有測試不動。新增單測：og fallback 解析（縮減 fixture）、
作者過濾（A 段污染案例）、exit code 分流。網路層維持不自動測（沿 repo 現狀），
真實 URL 手動 smoke 標 `[~]` deferred，verify §7 記錄對應覆蓋。

**§6 風險**：
- Meta 再改行動版政策 → 降級鏈 + drift dump 是設計答案；og meta 比 Relay 穩定。
- 行動版 Relay 結構邊角差異（多圖、引用貼文）→ smoke 時抽驗。
- 節流不變（呼叫端既有保守節奏），匿名行動 UA 不新增帳號風險。
