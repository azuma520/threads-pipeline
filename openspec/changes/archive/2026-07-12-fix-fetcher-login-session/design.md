# Design：修復 fetcher 登入態

## Context

`fetch_threads_post.py`（508 行）是 threads-pipeline 抓取任意公開 Threads 貼文的腳本：Playwright 開匿名行動版 context → 抓頁面 HTML → 從 `<script data-sjs>` 抽 Relay JSON → walk/classify/filter → render Markdown。既有 spec `threads-post-fetching` 定義四條 requirement（匿名指紋、主作者過濾、og fallback、exit code 三態）。

2026-07-12 確診：Threads 對匿名訪客一律回登入頁本體，Relay 與 og 皆無內容。這是伺服器端 session 檢查（非指紋），2026-07-05 的指紋偽裝修復已失效。上游決策經四輪 Codex 諮詢 + oEmbed curl 實測 + 使用者裁決收斂（見 brainstorm.md）。

**約束**：
- Windows 環境（profile lock、路徑、Singleton 殘留要處理）
- 用使用者本尊 Threads 帳號，Meta 條款禁未授權自動化收集——風險自主承擔，靠使用方式降險
- Relay 解析邏輯（~350 行）完好，不動
- 既有 exit 2 語意（schema drift dump）不得改變——維運依賴它

## Goals / Non-Goals

**Goals**
- fetcher 帶登入 session 抓取，恢復單條自動化
- 登入失效可偵測、可熔斷（exit 4），不與 schema drift 混淆
- profile 隔離、單實例鎖，Windows 可靠
- 指紋一致性（棄行動 UA 偽裝），降低裝置屬性跳變

**Non-Goals**
- vault 端 line-import／source-capture 路線改版與完整性狀態（Change A，skill-dev schema）
- claude-in-chrome 批次佇列與分塊協定（Change A）
- 無人排程、速率配額自動化（守則層）
- 小號、storage_state、CDP 方案（已評估否決）

## Decisions

### D1：登入態方案用 `launch_persistent_context` + 專用 profile
選 persistent context 而非 storage_state（次選）或 CDP（否決）。理由：
- persistent profile 保存 cookie/localStorage/IndexedDB，Meta 輪替 session 時正常瀏覽即回寫，維護最省心
- storage_state 需每次抓取後重匯出，且 sessionStorage 不原生持久化（Threads 是否依賴＝不確定），JSON 是可冒用 bearer credential 外洩半徑更大
- CDP 掛真實 Chrome 會暴露日常 profile（信箱/雲端/付款 session），Chrome 136+ 對預設 data dir 已限制 remote-debugging，fidelity 也較低
- 對現有 `fetch_page()` 改動最小：只換 browser/context 建立方式

profile 路徑：repo 外絕對路徑（如 `%LOCALAPPDATA%\threads-pipeline\threads-profile`），不放 OneDrive/雲同步/Git repo。

### D2：棄用行動版 UA 偽裝，改 Chromium 預設一致
`mobile_context_kwargs()` 現用 iPhone iOS Safari UA + `is_mobile=True`。登入態下，UA 宣稱 Mobile Safari 但實際是 Chromium＝跨引擎不一致，反而是風控訊號。改為登入與抓取用同一專用 headed Chromium，保持預設 UA/locale/timezone 大致一致。不加 canvas/webdriver spoofing（解不了 session 門檻，且提高規避意圖）。

### D3：新增 exit 4 = auth required，與 exit 2 分離（Review 修訂）
`detect_auth_failure(final_url, html, *, requested_url=None) -> str | None` 判定登入失效。**通用訊號**：`og:title` 登入字樣、final URL 含 `/login|/checkpoint|/challenge`、頁面含登入表單（密碼欄位）。**情境化訊號**（僅抓貼文時，見下方修訂段）：`og:url` 指向首頁、final_url 不含 requested code。命中 → exit 4，不 dump 成 schema drift。exit 2 保留給「真的 Relay 抽不到且非登入失效」。不自動填密碼、不循環重登。

**Review 修訂（Codex #1/#5、複審 C1/M1）**：
- **不得僅憑 final URL 落在首頁 path 判 auth**——登入用戶正常瀏覽首頁 final_url 也是首頁，會誤判。移除「path==`/` → auth_required」。
- **detector 情境化**：`detect_auth_failure(final_url, html, *, requested_url=None)`。通用訊號（auth path、og:title 登入字樣、登入表單）兩情境皆用；情境化訊號（og:url 指向首頁、final_url 已不含 requested 貼文 code＝被重導離開）**僅當 requested_url 可解析出貼文 code 時啟用**。抓貼文傳 `requested_url=url`；auth-check goto 首頁（requested 無 code）不啟用情境化訊號，故已登入首頁正確回 None（複審 C1）。「被重導離開貼文」的 redirect guard 即由此情境化涵蓋，不需 main 另接線（複審 M1）。
- **og 解析用擴充後的 `_OGMetaParser`（同時取 title + url），不用脆弱內聯 regex**——既有測試要求容忍屬性反序與單引號（`test_extract_og_fields_*`）。

**Dogfood 修訂（2026-07-12）**：實測發現 og:title「Threads • 登入」是 root 路徑靜態 crawler tag，已登入首頁同樣出現，導致 auth-check 誤回 4。新增正向身分訊號：HTML 含非零 `NON_FACEBOOK_USER_ID`／`IG_USER_EIMU` 直接判 session 有效（auth path 訊號除外——checkpoint 優先）。匿名頁該標記為 "0" 或缺席（實測對照）。風險：標記名屬 Meta 內部實作，改版可能失效——失效時退化為原 og:title 行為（誤判 4，fail-safe 方向安全）。

### D3b：新增 exit 5 = operational 失敗（Review 修訂，Codex #6）
profile 被占用（ProfileLock RuntimeError）、Playwright 啟動失敗等受控環境錯誤，SHALL 由 `main()` 捕捉轉為 exit 5，不得落入 exit 1（bad URL）或 exit 2（內容失敗），不得以未捕捉 traceback 非零結束。呼叫端據此區分「可重試 operational」與「真正內容失敗」。

### D4：`fetch_page()` 回傳 tuple → `FetchResult` dataclass
現回 `(html, screenshot)`。新增 `final_url`、`auth_status` 需求使 tuple 擴張難維護。改 dataclass：
```python
@dataclass
class FetchResult:
    html: str
    screenshot: bytes | None
    final_url: str
    auth_status: Literal["ok", "auth_required"]  # 收窄型別（複審 M2），拼字錯不靜默落 ok
```

### D5：og partial 徹底移除（Review 修訂，Codex #2；使用者裁決）
原設計「og fallback 降語意保留 exit 3 partial」與 spec「MUST NOT 產 partial」衝突。使用者裁決**徹底移除 og partial**：
- 刪除 `render_partial_markdown` 的 exit-3 呼叫路徑，exit 3 停用（退出碼契約改 0/4/2/1/5）。
- Relay 失敗時：`fetch_og_fallback` 若保留，僅作登入牆診斷——og 顯示登入牆 → exit 4；否則走既有 exit 2 內容失敗 dump。
- 既有 `test_main_og_fallback_exits_3` 改為驗證「不產 partial 輸出」。
- 理由：有登入 session 時主管道即應成功，登入態下 og partial 無意義；且登入後頁面 og 含個人化資料，落盤有風險。

**Dogfood 修訂 2（2026-07-12）**：實測死貼文（登入態重導作者頁）被 og 診斷誤報 exit 4。匿名 og 對貼文頁一律回登入牆（零資訊量），且 auth 失效已由主抓取 `auth_status` 上游攔截——og→4 分支邏輯上不可能正確觸發。`fetch_og_fallback` 連同 `MOBILE_UA` 全數移除，relay-miss 一律 exit 2（stderr 對重導案例加 GONE 提示助 triage）。

### D6：CLI 新增旗標，預設改 headed（Review 修訂，Codex #3/#4/#10）
新增 `--login`、`--profile PATH`、`--headless`、`--auth-check-only`。正常抓取預設 headed。Review 修訂：
- **位置參數 `url` 改 `nargs="?"`**——`--login`/`--auth-check-only` 不需 URL，一般模式缺 URL 才報錯（exit 1）。
- **`_default_profile_dir()` 使用 `os`，實作前確認 `import os`**（既有 import 區無 os）。
- **`--auth-check-only` 用頁面登入牆/表單訊號判定，不用首頁 URL 本身**（見 D3）。
- **debug HTML dump 改可選**：新增 `--debug-dump` 旗標，預設**不**建立 `_debug`／不寫檔（登入後頁面含個人化資料）；僅顯式啟用時才 dump。

## Risks / Trade-offs

- **[帳號封鎖/checkpoint 風險]** → 使用方式降險：僅人工觸發單條、headed、序列 + 10–20s 抖動 + 指數退避、每日低額上限、遇 429/登入頁/checkpoint 立即停；帳號出現警告即回報並暫停路線。無法消除政策風險，屬自主承擔。
- **[Threads Relay/DOM 改版致靜默少抓]** → invariant 兜底：selector 空結果不得轉成功、post code 須唯一定位、作者三處一致；不成立即報錯（非靜默）。
- **[profile 被併發占用/Singleton 殘留]** → 單實例鎖 + 明確錯誤；不直接刪整個 profile（先確認無殘留 process）。
- **[profile 是完整登入憑證]** → repo 外、ACL、不進 Git、不放雲同步；備份自負。
- **[Playwright bundled Chromium 升級致 profile migration]** → 固定 Playwright 版本，升級前備份人工驗證。
- **[headed 是否比 headless 更安全＝不確定]** → 保守先 headed（使用者可見），但 headed≠真人≠安全。

## Migration Plan

1. 先實作 `detect_auth_failure()` + `FetchResult` + exit 4（可獨立測試，不動抓取路徑）
2. 改 `mobile_context_kwargs()` → 登入 context kwargs；`fetch_page()` 用 persistent context
3. 加 `--login`/`--profile`/`--headless`/`--auth-check-only` 與 profile lock
4. `fetch_og_fallback()` 降語意
5. 改寫既有匿名相關測試（`test_mobile_context_kwargs_is_anonymous_mobile` 等），新增 auth-failure/exit 4/lock 測試
6. 使用者一次性 `--login` 建 profile → `--auth-check-only` 驗證 → 單條實測
7. **回滾**：profile 方案失效可暫退回舊匿名碼（git revert），但匿名已死，回滾僅為隔離問題非長期路線

## Open Questions

- `channel="chrome"`（需目標機裝 Chrome）vs bundled Chromium（可重現性佳）何者更不易觸發 Meta 驗證＝不確定。先用 bundled，實測後可調。
- 每日抓取量安全門檻具體數字＝不確定，保守從個位數起。
- Threads 有效登入態是否依賴 sessionStorage（影響若未來想加 storage_state 備援）＝不確定，本 change 不涉及。
