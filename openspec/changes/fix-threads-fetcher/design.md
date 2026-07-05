# Design: fix-threads-fetcher

## Context

`scripts/fetch_threads_post.py` 是獨立 CLI 腳本（repo 內無生產呼叫者），供 vault 端 line-import / source-capture 以子程序呼叫，把任意公開 Threads 貼文抓成 `drafts/library/{date}_{author}_{code}/` 四檔輸出（post.md / meta.json / relay.json / screenshot.png）。

2026-07-05 確診：匿名桌面 context 開貼文 URL 被 302 到 logged-out feed（`BarcelonaLoggedOutFeedContainerQuery` ×8、無 `BarcelonaPostPageDirectQuery`），屬 Threads 端政策改變、非限流。官方 API 無法替代（keyword_search Standard Access 限自己貼文、oEmbed 零內文、profile_discovery 需 Advanced Access 未過審）。

當場實測（首樣本 `@lingyu9683/post/DISnS0JJywN`）：
- 純 curl 桌面 UA：空殼頁 ❌
- 純 curl 行動 UA：無 Relay payload，但 `og:title`/`og:description` 含實際內文（~151 字疑似截斷、無自串）⚠️
- **Playwright + 行動 UA + `is_mobile`：完整 Relay，`walk_posts` 抽出 27 posts，A+B 內文完整 ✅**
- 附帶發現：行動版頁面載「相關串文」，他人頂層貼文混入且被 classify 標 A（需防護）

**擴大實測（2026-07-05，另抽 7 條真實 pending URL、7 個不同作者）**：主管道 7/7 全成功（連同首樣本 = 8/8），節點數涵蓋單則到 22 節點長串、有自串與無自串型態；A 段主文皆完整無截斷（80–366 字）；**A_foreign 全 0、logged-out 導向全 0**；序列跑每條間隔 7 秒無風控。結論修正兩點：(1) 核心修法穩定性由 n=1 提升到 n=8 實證；(2) **相關串文污染是偶發**（僅首樣本熱門貼文觸發），防護仍保留（成本低、確實會發生）但非常態。og fallback 降級鏈本批未觸發（主管道全成功），仍為 n=0 實跑，屬保險絲路徑。

約束：使用者定位為長期管道；盡量不用登入態（帳號風險隔離）；解析層有完整單測、網路層零測試（沿現狀）；輸出契約不可破壞。

## Goals / Non-Goals

**Goals:**
- 恢復匿名抓取能力（主管道：行動版 context）
- 斷供韌性：主管道死時降級 og fallback，保住 headline（partial 而非全損）
- 防止相關串文污染輸出
- 明確的退出碼契約供呼叫端分流（0 完整 / 3 partial / 2 全失敗）

**Non-Goals:**
- 不做登入態抓取（最後手段，本 change 不碰）
- 不動 vault 端 line-import / source-capture（partial 接線屬 vault 後續小修）
- 不改解析層演算法與輸出目錄結構
- 不新增節流機制（呼叫端既有保守節奏）

## Decisions

### D1：主管道用行動版瀏覽器指紋，不用登入態
- **選擇**：`new_context(user_agent=MOBILE_UA, viewport={"width":390,"height":844}, is_mobile=True)`；`MOBILE_UA` 為模組層常數（iPhone Safari 字串）
- **理由**：實測唯一完整可用的匿名支線；登入態風險掛帳號（官方 API token 綁真帳號，風控波及發文管道）
- **已考慮 alternative**：(a) 登入態 storage_state——使用者裁定最後手段；(b) oEmbed——2026-04-23 已實測零內文；(c) 第三方鏡像——存活不穩、引入外部信任問題，未採

### D2：降級鏈用純 HTTP GET 抓 og meta，不開第二個 browser
- **選擇**：Relay 抽取失敗時，用 stdlib（`urllib.request`）帶行動 UA GET 一次，正則抽 `og:title`/`og:description`；正則放寬對屬性順序的假設（`property`/`content` 任一在前皆匹配），避免 Meta 微調 meta 標籤即整條降級失效
- **理由**：og meta 在純 curl 行動 UA 下可得（實測）；SEO 資產比 Relay schema 穩定；不開 browser 成本低、依賴零新增
- **已考慮 alternative**：Playwright 重試不同 UA——成本高且失敗模式相同；requests 套件——非既有依賴，stdlib 足夠

### D7：og fallback 成功需通過 author guard，否則視為抓錯頁 → exit 2
- **選擇**：og fallback 只有在 `og:title` 含 `(@{url_author})` 時才算 partial 成功（exit 3）；否則視為抓到 logged-out feed / 錯誤頁 / 通用 SEO 文案，走既有 drift dump + exit 2 路徑
- **理由**（**採納 Codex gpt-5.5 審查阻斷性 ①**）：原設計「og:description 非空即 partial」太寬——logged-out feed 頁、錯誤頁也可能帶通用 og meta，會把「主管道壞損」偽裝成 partial 成功，讓 `_debug` dump 與 exit 2 告警靜默消失。這違反「指針可爛、貨不能丟」的反面戒律：partial 不得吃掉主管道壞損信號（「假高品質比明說品質低更糟」）。實測 og:title 形如 `澤哥…(@lingyu9683) on Threads`，含 `(@username)`，guard 成本極低
- **已考慮 alternative**：驗 og:description 對得上 code——og:description 不含 code，無法直接驗；只驗非空——即被否決的原設計

### D3：partial 輸出沿用既有目錄契約，靠標記區分
- **選擇**：og fallback 成功時照常寫輸出目錄；`meta.json` 加 `fetch_mode: "og_fallback"`、`post.md` frontmatter 加 `partial: true`；不寫 relay.json
- **理由**：呼叫端已認識目錄結構，最小驚訝；「指針可爛、貨不能丟」——摘要好過全損
- **已考慮 alternative**：另立 partial 目錄命名——破壞輸出契約，呼叫端要學新規則，拒

### D4：退出碼 0 / 3 / 2 三態
- **選擇**：`0` 完整成功；`3` partial 成功（新增）；`2` 連 og 都拿不到（維持既有 drift dump + exit 2）
- **理由**：呼叫端可用退出碼分流狀態，不用解析輸出；`2` 語意不變保住既有呼叫端行為
- **已考慮 alternative**：partial 也回 0 靠 meta.json 區分——呼叫端靜默把 partial 當完整入庫，違反明說品質原則，拒

### D5：污染防護錨在主文作者
- **選擇**：從 URL 解析 `main_author`，A 段（主文）只保留 `username == main_author` 的節點；B/C 段語意本綁作者；D 段（他人頂層回覆）維持既有邏輯
- **理由**：實測行動版頁面「相關串文」的他人貼文被 classify 標 A，會污染 post.md 主文段。擴大實測顯示此污染為**偶發**（8 條僅首樣本觸發），但成本低且確實會發生，防護保留
- **已考慮 alternative**：改 classify 本體——影響面大且既有測試全綁現行語意，在 filter 層處理更小創面
- **實作前置**：先加測試確認 classify 對他人頂層非回覆貼文的實際行為，防護加在正確的層
- **已知邊界**（Codex 建議 ③）：`username == main_author` 擋不了「同作者但非本串」的推薦貼文。實測 8 條未觀察到此情形；apply 時檢查 Relay 是否有 thread root / permalink 欄位可用 `code` 進一步錨定主串，有才加、無則接受此邊界並記錄

### D6：網路層維持不自動測
- **選擇**：新增測試全在純函式層（og 解析、作者過濾、exit code 分流邏輯）；`fetch_page` 仍無自動測試，真實 URL 手動 smoke 標 `[~]` deferred
- **理由**：沿 repo 現狀（解析層全測、網路層零測）；mock chromium 的維護成本高於價值
- **已考慮 alternative**：playwright mock / 錄放——過度工程，拒

## Risks / Trade-offs

- [Risk] Meta 再改行動版匿名政策 → Mitigation: og fallback 降級鏈 + 既有 `_debug` drift dump（exit 2 時 dump HTML），斷供時保 headline 且告警明確。降級鏈本身受 D7 author guard 保護，不會把壞損頁偽裝成 partial
- [Risk] og fallback 降級鏈 n=0 實跑（主管道太穩，本輪未觸發）→ Mitigation: exit 3 路徑以 monkeypatch 單測覆蓋（plan Task 7），首次真實觸發時人工確認一次
- [Risk] 行動版 Relay 結構與桌面版有邊角差異（多圖、引用貼文、影片）→ Mitigation: 手動 smoke 抽驗多型態貼文；解析層既有測試守住核心路徑
- [Risk] og:description 截斷（~150 字）且無 B 段 → 接受理由：partial 本來就是降級語意，明確標記讓呼叫端與使用者知道品質等級
- [Trade-off] exit 3 在 vault 端接線前可能被 runner 當失敗處理 → 接受理由：當失敗處理是安全方向（重試不入庫），接線屬 vault 後續小修；記入 Migration Plan

## Migration Plan

1. 本 repo：實作 + 測試 + 手動 smoke（真實 URL 抽驗 3-5 條不同型態貼文）
2. 部署 = merge 到 main（腳本被 vault 端以路徑呼叫，無發佈步驟）
3. vault 端補跑：`runner.py --batch threads`（45 條 pending 全是 `failed_transient`，自動重試）
4. vault 端後續小修（不在本 change）：line-import runner 辨識 exit 3 / partial 標記，staged 目錄註記 partial；source-capture 同理
5. Rollback：git revert 單檔腳本即可，無狀態遷移

## Open Questions

- ~~classify 對「他人頂層非回覆貼文」的實際回傳~~ **已決議（Codex ⑦）**：實作前以 characterization test（plan Task 1）釘住現行回傳 A，據此把防護加在 filter 層（`drop_foreign_main_posts`）；若測出非 A 則回修 D5
- 同作者非本串推薦貼文的錨定（見 D5 已知邊界）——apply 時視 Relay 欄位決定，非阻斷
- og fallback 對影片型/純圖型貼文的 og:description 內容品質——smoke 時觀察，必要時在 partial 輸出註記媒體型態
