# threads-post-fetching Delta Spec

> Review 修訂（Codex gpt-5.6-sol，2026-07-12）：requirement identity 對齊 openspec 慣例——變動用原名 MODIFIED、換掉的 REMOVED、新的 ADDED，不改名合併。og partial 徹底移除（使用者裁決）；operational failure 新增 exit 5。

## ADDED Requirements

### Requirement: Authenticated persistent-profile fetch
`fetch_threads_post.py` 的主管道 SHALL 以帶登入 session 的專用 persistent browser profile 開啟貼文頁。fetcher SHALL 使用 `launch_persistent_context` 綁定 repo 外的專用 `user_data_dir`，SHALL 保持 Chromium 預設指紋一致（登入與抓取共用同一 profile），MUST NOT 套用行動版 UA 偽裝或其他 fingerprint spoofing。fetcher SHALL 對同一 profile 強制單實例（併發啟動 SHALL 以明確錯誤拒絕並以 operational 退出碼結束）。

#### Scenario: 帶登入 session 抓取公開貼文成功
- **WHEN** 專用 profile 已含有效登入 session，以公開貼文 URL 呼叫 fetcher
- **THEN** `extract_relay_json` SHALL 取得含 `BarcelonaPostPageDirectQuery` 資料的 Relay payload，並產出 `post.md` + `meta.json` + `relay.json`（`screenshot.png` 依 `--no-screenshot` 參數可選），退出碼 0

#### Scenario: Relay 尚未載入完成
- **WHEN** 頁面已出現 `<script data-sjs>` 但尚未含 `BarcelonaPostPageDirectQuery` post payload
- **THEN** fetcher SHALL 輪詢重試 `extract_relay_json` 至逾時，MUST NOT 在首個 `data-sjs` 出現即擷取並誤判為抽取失敗

#### Scenario: profile 已被占用
- **WHEN** 同一 `user_data_dir` 已被另一 instance 使用時再次呼叫 fetcher
- **THEN** fetcher SHALL 以明確錯誤訊息與 operational 退出碼（5）拒絕啟動，MUST NOT 破壞既有 profile

### Requirement: Login-session failure detection
fetcher SHALL 具備判定登入失效與驗證挑戰的能力。**通用訊號**（不分情境）：final URL 含 `/login`｜`/checkpoint`｜`/challenge`、`og:title` 為登入字樣、或頁面含登入表單（如密碼欄位）。**正向身分訊號（優先於 og:title／表單訊號，次於 auth path 訊號）**：頁面 HTML 含非零 viewer 身分標記（`NON_FACEBOOK_USER_ID`／`IG_USER_EIMU`）時 SHALL 判為 session 有效（非 auth-required）——og:title 登入字樣對 threads.com 根路徑為靜態 crawler 標記，已登入頁面亦會出現（2026-07-12 dogfood 實證），MUST NOT 單獨憑 og:title 判定已登入頁面為失效。auth path 訊號（`/login`｜`/checkpoint`｜`/challenge`）不受正向訊號覆蓋——已登入但被挑戰仍 SHALL 判 auth-required。**情境化訊號**（僅當本次請求目標為「貼文」時啟用）：`og:url` 指向首頁、或 final URL 已不含所請求貼文的 code（＝被重導離開貼文）。命中任一有效訊號 SHALL 判為 auth-required 並以退出碼 4 結束。判定 MUST NOT 僅憑 final URL 落在首頁 path 即認定失效；且當請求目標非貼文（如 `--auth-check-only` 開啟首頁）時 MUST NOT 以「og:url 指向首頁」判定失效——登入用戶正常瀏覽首頁不得誤判。fetcher MUST NOT 自動填入帳密或 2FA、MUST NOT 對登入失效循環重試。og:title／og:url 解析 SHALL 容忍 meta 屬性順序與單雙引號差異。

#### Scenario: 抓取遇 checkpoint 挑戰
- **WHEN** 抓取導向 `/checkpoint/` 或 `/challenge/` URL
- **THEN** 判定 SHALL 回報 auth-required，fetcher SHALL 以退出碼 4 結束且不自動處理挑戰

#### Scenario: 登入用戶抓取正常貼文不誤判
- **WHEN** profile 已登入，抓取的 final URL 為正常貼文頁且無登入牆/表單
- **THEN** 判定 SHALL 回報非 auth-required，fetcher SHALL 續行 Relay 抽取

#### Scenario: session 有效性檢查
- **WHEN** 以 `--auth-check-only` 呼叫 fetcher
- **THEN** fetcher SHALL 依頁面登入牆/表單訊號（非首頁 URL 本身）判定 session 是否有效並回報（0=有效 / 4=需登入），MUST NOT 產出內容輸出

#### Scenario: 已登入首頁不因靜態 og:title 誤判
- **WHEN** profile 已登入，`--auth-check-only` 開啟首頁，頁面 og:title 為「Threads • 登入」（靜態標記）且 HTML 含非零 viewer 身分標記
- **THEN** 判定 SHALL 回報 session 有效，fetcher SHALL 以退出碼 0 結束

### Requirement: Login initialization CLI
fetcher SHALL 提供 `--login` 旗標開啟 headed 瀏覽器供使用者本人完成一次登入以初始化 profile，SHALL 提供 `--profile PATH` 指定 profile 目錄，SHALL 提供 `--headless` 使抓取以無頭模式執行（預設 headed），SHALL 提供 `--auth-check-only` 僅驗證 session。位置參數 `url` SHALL 為可選（`nargs="?"`）——`--login`／`--auth-check-only` 模式不需 URL；一般抓取模式 SHALL 於缺 URL 時報錯（退出碼 1）。`--login` MUST NOT 進入 Relay／輸出管線。

#### Scenario: 首次登入初始化（無 URL）
- **WHEN** 以 `--login`（不帶 URL）呼叫 fetcher
- **THEN** fetcher SHALL 開啟 headed 瀏覽器讓使用者登入，登入完成後保存 session 至 profile，MUST NOT 嘗試抓取或輸出，且 MUST NOT 因缺 URL 而報錯

## MODIFIED Requirements

### Requirement: Exit code contract
fetcher SHALL 以互斥退出碼表達執行結果，`0` 表示**所選執行模式成功**（一般抓取＝Relay 完整成功；`--auth-check-only`＝session 有效；`--login`＝登入初始化完成）；`4` = 登入失效／checkpoint（需重新登入）；`2` = 內容全失敗（Relay 抽不到且非登入失效，含 drift dump）；`1` = 使用參數錯誤（URL 解析失敗、一般模式缺 URL、或 argparse usage error）；`5` = operational 失敗（profile 被占用、瀏覽器啟動失敗等受控環境錯誤）。退出碼 `2` 既有語意（schema drift 內容失敗）MUST NOT 改變；`4` MUST NOT 與 `2` 混用；argparse usage error MUST 映射為 `1`（MUST NOT 沿用 argparse 預設的 `SystemExit(2)`）；operational 失敗 MUST NOT 落入 `1` 或 `2`，SHALL 由 `main()` 最外層統一捕捉**界定的 operational 例外**（profile lock 占用、I/O 錯誤、瀏覽器引擎錯誤）轉為受控的 `5`（涵蓋 login／fetch／輸出／debug dump 全部 I/O），MUST NOT 以未捕捉 traceback 結束。程式缺陷例外（如 `TypeError`／`KeyError`／`AssertionError`）MUST NOT 被偽裝成 `5`（避免測試假綠、真 bug 被藏）。

**Reason**: 匿名 og partial 路徑移除後 exit 3 停用；登入失效（4）與 operational 失敗（5）需與內容失敗（2）、參數錯誤（1）分離，否則呼叫端無法分流。`0` 因引入多模式而語意擴為「模式成功」，呼叫端須先知道自己下的模式再解讀 0。

**Migration**: 呼叫端移除對 exit 3 的處理；新增對 4（暫停路線/提示重登）與 5（可重試 operational）的分流；解讀 0 時綁定所下模式。

#### Scenario: 退出碼互斥可分流
- **WHEN** 同一次執行以特定模式結束
- **THEN** fetcher SHALL 回傳 `0`/`4`/`2`/`1`/`5` 其中恰一個，使呼叫端能結合「所下模式 + 退出碼」區分模式成功／登入失效／內容失敗／參數錯誤／operational 失敗

#### Scenario: argparse usage error 不撞內容失敗碼
- **WHEN** 傳入未知旗標或缺少選項值等 argparse usage error
- **THEN** fetcher SHALL 以退出碼 `1` 結束，MUST NOT 以 argparse 預設 `2` 結束（避免與內容失敗混淆）

## REMOVED Requirements

### Requirement: Mobile browser fingerprint for anonymous fetch
**Reason**: Threads 伺服器端 session 檢查使匿名抓取失效；行動 UA 偽裝在登入態下成為跨引擎不一致的風控訊號。由 "Authenticated persistent-profile fetch" 取代。

**Migration**: `mobile_context_kwargs()` 改為 `authenticated_context_kwargs()`（棄 `MOBILE_UA`／`is_mobile`）；既有匿名測試（如 `test_mobile_context_kwargs_is_anonymous_mobile`）改寫為驗證登入 context 不帶行動偽裝。

### Requirement: OG metadata fallback on Relay failure
**Reason**: 登入態改版後，Relay 失敗時的匿名 og partial 已無意義（有登入 session 時主管道即應成功），且登入後頁面 og 可能含個人化資料；partial 成功語意會掩蓋真正失敗。匿名 og 若顯示登入牆，改由 "Login-session failure detection" 判為 exit 4；否則走既有 exit 2 內容失敗。（2026-07-12 dogfood 追加：匿名 og 對貼文頁一律回登入牆，登入牆診斷零資訊量且將死貼文誤報為 auth 失效，og fallback 含診斷用途全數移除；relay 缺席時 session 有效性已由主抓取的 auth 偵測保證，逕行 exit 2）

**Migration**: 移除 `render_partial_markdown` 的 exit-3 呼叫路徑；`fetch_og_fallback` 若保留僅作登入牆診斷，MUST NOT 產出 partial 輸出。既有 `test_main_og_fallback_exits_3` 改為驗證「不產 partial 輸出」（exit 2 或 4）。（2026-07-12 追加：移除 `fetch_og_fallback` 與其呼叫點；relay 缺席 → exit 2）
