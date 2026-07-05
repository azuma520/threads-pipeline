# Tasks: fix-threads-fetcher

## 1. 前置驗證（classify 行為確認）

- [ ] 1.1 加測試釘住 classify 對「他人頂層非回覆貼文」的實際回傳（A 或 D），據此確定作者過濾防護的實作層（filter_by_flags 或其前後）

## 2. 主管道修復

- [ ] 2.1 `fetch_page()` 改行動版 context：模組層常數 `MOBILE_UA`（iPhone Safari）、viewport 390×844、`is_mobile=True`；維持匿名與 launch/close 生命週期
- [ ] 2.2 作者過濾防護：從 URL 解析 `main_author`，A 段只保留主文作者節點；附污染案例單測（fixture 含他人頂層貼文）

## 3. og fallback 降級鏈

- [ ] 3.1 新增 og fallback：stdlib HTTP GET（行動 UA）→ 正則抽 `og:title`/`og:description`（含 HTML entity unescape）；附縮減 fixture 單測
- [ ] 3.2 partial 輸出：沿用輸出目錄契約，`meta.json` 標 `fetch_mode: "og_fallback"`、`post.md` frontmatter 標 `partial: true`、不寫 relay.json；附單測
- [ ] 3.3 exit code 三態接線：0 完整 / 3 partial / 2 全失敗（維持既有 drift dump）；附分流邏輯單測

## 4. 驗證與收尾

- [ ] 4.1 全測試套件通過（既有解析層測試零回歸）
- [ ] 4.2 手動 smoke：真實 URL 抽驗 3-5 條不同型態貼文（純文字、多圖、影片、含自串），確認 A+B 完整與 partial 路徑；記錄於 verify（deferred 標 `[~]` 規則適用）
- [ ] 4.3 docstring / README 段落更新（行動版指紋、退出碼契約、partial 語意），Migration note 寫明 vault 端接線待辦
