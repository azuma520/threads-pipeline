# Tasks：修復 fetcher 登入態

> 已納入 Codex gpt-5.6-sol 規劃審查 10 條修訂（2026-07-12）。詳細 micro-steps 見 plan.md。

## 1. OG parser 擴充 + 登入失效偵測 + FetchResult
- [x] 1.1 補 `import os`、`from dataclasses import dataclass`
- [x] 1.2 擴充 `_OGMetaParser` 納入 og:url；新增 `extract_og_meta`（不要求 description）
- [x] 1.3 `detect_auth_failure(final_url, html)`：auth path / og:title 登入字樣 / og:url 首頁 / 登入表單——**不用 final-url 首頁 path**（誤判登入用戶）
- [x] 1.4 `FetchResult` dataclass + `_default_profile_dir()`
- [x] 1.5 測試全綠（每 commit 跑完整測試檔）

## 2. persistent context 抓取 + Relay 輪詢 + profile 鎖
- [x] 2.1 `mobile_context_kwargs()` → `authenticated_context_kwargs()`（棄行動偽裝）
- [x] 2.2 `ProfileLock` 單實例鎖（lockfile，非 SingletonLock）
- [x] 2.3 `fetch_page()` 用 `launch_persistent_context`，profile_dir 有預設，**輪詢 `extract_relay_json` 至逾時**（非首個 data-sjs），回 `FetchResult`
- [x] 2.4 同步接 main 呼叫 + 遷移既有 main 測試 monkeypatch（避免中間壞版本）

## 3. CLI 參數（url 可選）+ exit 4/5 契約
- [x] 3.1 argparse：`url` 改 `nargs="?"`，新增 `--profile/--headless/--login/--auth-check-only/--debug-dump`
- [x] 3.2 一般模式缺 URL → exit 1
- [x] 3.3 exit 4 auth-required 接線
- [x] 3.4 operational 例外捕捉 → exit 5（ProfileLock/瀏覽器失敗，不落 1/2）

## 4. 早退分支 + og partial 移除 + debug 旗標
- [x] 4.1 `run_login` + `--login` 早退（不進抓取管線）
- [x] 4.2 `--auth-check-only` 用登入表單訊號判定（非首頁 URL），回 0/4
- [x] 4.3 **移除 og partial**：刪 exit-3 路徑與 `render_partial_markdown` 呼叫；改寫 `test_main_og_fallback_exits_3` 為「不產 partial」
- [x] 4.4 debug HTML dump 改 `--debug-dump` 旗標（預設不 dump/不建 _debug）

## 5. 清理殘留 + 文件
- [x] 5.1 刪 `test_mobile_context_kwargs_is_anonymous_mobile` 等匿名殘留；確認無孤兒引用
- [x] 5.2 確認既有 Relay/render/classify 測試全綠
- [x] 5.3 更新 README / CLAUDE.md（fetcher 及測試、CLI 用法、exit code 表 0/4/2/1/5、profile 建立）

## 6. 使用者 dogfood 實測（apply 末）
- [x] 6.1 `--login` 建 profile → `--auth-check-only` 驗證
- [x] 6.2 單條真實貼文抓取（含作者自回覆），exit 0
- [x] 6.3 空 profile → exit 4；併發 → exit 5

## 7. Dogfood 修訂：正向身分訊號（2026-07-12 發現）
- [x] 7.1 `detect_auth_failure` 加 `NON_FACEBOOK_USER_ID`/`IG_USER_EIMU` 非零正向訊號（auth path 優先權維持）
- [x] 7.2 回歸測試四條（已登入首頁誤判回歸、匿名 0 值、checkpoint 優先、EIMU 變體）
- [x] 7.3 spec/design 同步修訂

## 8. Dogfood 修訂 2：og 診斷死分支移除（2026-07-12 發現）
- [x] 8.1 relay-miss 分支移除 og fallback 呼叫與 exit 4 誤報，一律 exit 2＋GONE 提示
- [x] 8.2 刪 `fetch_og_fallback`／`MOBILE_UA` 死碼與對應測試；新增死貼文回歸測試
- [x] 8.3 spec/design 同步修訂
