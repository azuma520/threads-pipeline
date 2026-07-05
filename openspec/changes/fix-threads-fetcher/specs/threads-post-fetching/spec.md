# Delta Spec: threads-post-fetching

## ADDED Requirements

### Requirement: Mobile browser fingerprint for anonymous fetch
`fetch_threads_post.py` 的主管道 SHALL 以行動版瀏覽器指紋開啟貼文頁：`user_agent` 為模組層常數 `MOBILE_UA`（iPhone Safari 字串）、viewport 390×844、`is_mobile=True`，且 SHALL 維持匿名（無 cookie、無 storage_state）。

#### Scenario: 匿名抓取公開貼文成功
- **WHEN** 以公開貼文 URL 呼叫 fetcher 且 Threads 回應行動版貼文頁
- **THEN** `extract_relay_json` SHALL 取得含 `BarcelonaPostPageDirectQuery` 資料的 Relay payload，並產出 `post.md` + `meta.json` + `relay.json`（`screenshot.png` 依 `--no-screenshot` 參數可選），退出碼 0

### Requirement: Main-author filtering of A-segment posts
主文（A 段）SHALL 只包含 URL 中主文作者（`main_author`）的貼文節點；來自「相關串文」等推薦區塊的他人貼文 MUST NOT 出現在 A 段輸出。

#### Scenario: 行動版頁面混入相關串文
- **WHEN** 抓取的頁面 Relay 資料含其他作者的頂層非回覆貼文
- **THEN** 這些節點 SHALL 被排除於 A 段之外，post.md 主文段只含 `main_author` 的內容

### Requirement: OG metadata fallback on Relay failure
當主管道無法取得 Relay 資料時，fetcher SHALL 降級為單次純 HTTP GET（行動 UA、不開 browser），解析 `og:title` 與 `og:description`。partial 成功 SHALL 以 author guard 為條件：`og:title` 含 `(@{url_author})` 且 `og:description` 非空時，才產出 partial 輸出；partial 輸出 SHALL 沿用既有輸出目錄結構，`meta.json` SHALL 含 `fetch_mode: "og_fallback"`，`post.md` frontmatter SHALL 含 `partial: true`，且 MUST NOT 產出 relay.json。author guard 不通過時 fetcher SHALL NOT 產出 partial 輸出（避免 logged-out feed / 錯誤頁被偽裝成成功、掩蓋主管道壞損信號）。

#### Scenario: Relay 抽取失敗但 og meta 對得上作者
- **WHEN** 貼文頁拿不到 `BarcelonaPostPageDirectQuery` payload，但 og:description 非空且 og:title 含 `(@{url_author})`
- **THEN** fetcher SHALL 寫出標記 partial 的輸出目錄並以退出碼 3 結束

#### Scenario: Relay 失敗且 og 未通過 author guard（如 logged-out feed）
- **WHEN** 貼文頁拿不到 Relay，且 og:description 為空或 og:title 不含 `(@{url_author})`
- **THEN** fetcher SHALL NOT 產出 partial 輸出，SHALL dump 前 500KB HTML 到 `_debug/` 並以退出碼 2 結束

#### Scenario: 連 og meta 都拿不到
- **WHEN** 主管道與 og fallback HTTP GET 皆無法取得任何內容
- **THEN** fetcher SHALL 維持既有行為：dump 前 500KB HTML 到 `_debug/` 並以退出碼 2 結束

### Requirement: Exit code contract
fetcher SHALL 以互斥退出碼表達抓取結果三態：`0` = 完整成功（Relay 主管道）、`3` = partial 成功（og fallback 且通過 author guard）、`2` = 全失敗（含 drift dump）。既有退出碼 `2` 的語意 MUST NOT 改變。

#### Scenario: 三態退出碼互斥可分流
- **WHEN** 同一次執行結束
- **THEN** fetcher SHALL 回傳 `0`/`3`/`2` 其中恰一個，使子程序呼叫端能僅憑退出碼區分完整成功 / partial / 失敗而無需解析輸出檔（呼叫端如何辨識屬呼叫端責任，不在本 capability 範圍）
