<!--
Raw capture. 本 change 的設計探索不是走 superpowers:brainstorming skill，
而是 2026-07-12 在 vault 主 session 內經「四輪 Codex 諮詢 + oEmbed 實測 + 使用者裁決」
收斂而成（使用者明確選擇基於定稿手寫，見定稿 v3 決策依據段）。
本檔原樣捕捉該決策鏈；design.md 再萃取重組。
上游定稿：あずま的資料庫/7、專案/LINE收藏搶救/threads-fallback-design-draft-20260712.md
-->

# Brainstorm：修復 fetcher 登入態（raw capture）

## 背景 / 觸發事故

2026-07-12 LINE 收藏搶救，45 條 Threads 貼文卡住待抓。runner 試水溫 5/5 全敗（playwright timeout）。診斷確認 **Threads 匿名抓取已死**：

- fetcher dump 顯示 `og:title="Threads • Log in"`、`og:url=首頁`——伺服器對匿名訪客直接回登入頁本體，og 降級鏈無物可降。
- 2026-07-05 修過指紋偽裝（解「像不像正常瀏覽器」），當時有效、現在無效。門檻已變成「有沒有登入 session」（伺服器端身分檢查），非客戶端偽裝——偽裝無解。
- 對照組：同 URL 在已登入的 Chrome 看得到全文。

當時走 claude-in-chrome（登入 Chrome 人工路線）救回 36 活、判死 9，入池 24 條。事後定調：把經驗轉為機制優化，找第三方討論。

## 決策鏈

### Q1：匿名抓取還救得回來嗎？
不能。這是伺服器端 session 檢查，非指紋問題。修 `mobile_context_kwargs()` 的偽裝參數無效。**匿名管道葬送**，降格為診斷用途（辨識登入牆/404 頁型態）。

### Q2：官方 oEmbed 能不能當內容源或判活探針？
**不能。實測終結。** 兩輪 Codex 對 oEmbed 角色分歧（gpt-5.5 選不做、gpt-5.6-sol 引 2026-03 tokenless 傳聞選「留當判活探針」）。2026-07-12 curl 實測 `graph.threads.com/oembed`：
- `@leen_0622`、`@chinru.tw`（一般創作者）：一律 `code 24 OAuthException: The requested resource does not exist`，帶 201 字元自有 app token 亦同。
- `@zuck`：成功回 embed HTML。
結論：oEmbed 只對少數大帳號開放，對本 vault 使用情境無用。**不做**，連帶取消原「threads-cli post get-by-url」待辦。

### Q3：fetcher 的核心壞在哪？怎麼修？
壞在「沒帶登入」，不是抓取邏輯壞。Relay JSON 解析（walk_posts/classify/extract_relay_json 等 ~350 行）完好，原封保留。Codex（gpt-5.6-sol）讀 508 行後推薦方案比較：

| 方案 | 改動 | 過期維護 | Windows | 帳號風險 | 判定 |
|---|---|---|---|---|---|
| **launch_persistent_context ＋專用 profile** | 小～中 | 低 | 佳（profile lock 要處理） | 中～高 | **推薦** |
| storage_state JSON 匯出入 | 中 | 中～高 | 佳 | 中～高（＋檔案外洩） | 次選 |
| connect_over_cdp 掛真實 Chrome | 中～高 | 低 | 麻煩（Chrome 136+ 限制） | 高（日常 profile 全暴露） | 不推薦 |

選 **persistent context ＋專用 profile**：`--login` 開 headed 由使用者本人登入一次（含 2FA），session 由瀏覽器自然維護，cookie 輪替正常瀏覽即回寫，最省心。棄用 iPhone Safari UA（跨引擎不一致＝裝置屬性跳變），保持 Chromium 預設一致，不加指紋偽裝（穩定一致 > spoofing，且 spoofing 解不了 session 門檻）。

### Q4：用哪個帳號？
使用者初想小號（降後果）。分析：小號降「出事代價」但不降「被抓機率」（全新空號反而更易被風控盯），且 Threads 綁 IG、同機同 IP 難隔離，連坐不確定。使用者最終**裁決：直接用本尊帳號，不開小號**——省養號兩週，風控改靠使用方式（僅人工觸發單條、headed 可見、序列＋抖動、撞 checkpoint 即熔斷、不排程）。已知悉 Meta 條款禁未授權自動化收集，屬中度風險自主承擔。

### Q5：批次要不要也走修好的 fetcher？
不要（賭注是本尊帳號時）。批次是自動化偵測風險最高的型態。**分工定案**：
- source-capture 單條（低頻、指名）→ 修復後 fetcher（headed、人工觸發）
- line-import 批次 → claude-in-chrome（真實瀏覽器，帳號風險最低）
- fetcher 撞登入牆/checkpoint → 熔斷降到 claude-in-chrome，人工看一眼

### Q6：判死規則（Codex 抓到的 bug）
早期草案寫「匿名 fetch 重導＝貼文亡」——**錯**，活貼文對匿名訪客也回登入頁，會誤殺活帖永久放棄。修正：只有**登入狀態下**看到明確「不存在/已刪除」（排除 session 失效）才 `failed_terminal`；帳號亡需第二證據。匿名層只能標 `anonymous_inaccessible`，永不 terminal。

### Q7：exit code 怎麼接？
既有契約：0=完整、3=og partial 過 guard、2=全失敗（drift dump）、1=URL 壞。og fallback（R3）在新門檻下不再能取內容。新增 **exit 4 = auth required/checkpoint**（登入頁/og:url 首頁/`/login|/checkpoint|/challenge`/登入表單），**不得混入 exit 2**（維運會誤判成 schema drift）。exit 2 既有語意不變。

## 設計取捨與已知代價

- 本尊帳號自動化：條款風險自主承擔，靠低頻人工觸發＋熔斷降險。帳號出現 checkpoint/警告即回報並暫停路線。
- Threads Relay/DOM 改版會使腳本失效——靠 invariant 讓失效大聲報錯（selector 空結果不得轉成功），寧報錯不靜默少抓。
- 官方 API 對「他人貼文完整串含自回覆」無端點，此路線無官方替代品。
- fetch_page 回傳應從 tuple 升級 dataclass（FetchResult：html/screenshot/final_url/auth_status），容納 auth 狀態。
- fetch_og_fallback 保留但降語意（只診斷匿名入口是否恢復，不再宣稱 partial 內容）；debug HTML 改可選（登入後頁面含個人化資料，需權限與保存期控管）。

## 本 change 的邊界（Non-Goals）

- 不含 vault 端 line-import／source-capture 的路線改版與完整性狀態欄位（那是 vault repo 的 Change A，skill-dev schema）。
- 不含 claude-in-chrome 批次佇列與分塊協定（Change A 範圍）。
- 不做無人排程、速率配額自動化（守則層，非本次 code 範圍）。
- 不做小號、不做 storage_state/CDP 方案。
