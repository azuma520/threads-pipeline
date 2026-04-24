# Demo Script — `threads_profile_discovery`

> **本輪送審**（2026-04-23 重送範圍 3 個之一）
>
> 診斷結果：`/{username}` 與 `/{username}/threads` 在 `profile_discovery` 核准前**完全鎖住**，對自己帳號亦同（`probe_profile_discovery.py` verdict = `ENDPOINT_LOCKED`；Graph API 回 `Object with ID '{username}' does not exist, cannot be loaded due to missing permissions` / HTTP 400）。
>
> **本輪錄影採 Plan B（Architecture-Demo with honest disclosure）** ——結構與 `demo-script-manage-mentions.md` Plan B 對齊；核心訊息「CLI 與整合已實作、endpoint 在 Meta docs 定義明確、use case 真實存在、endpoint 回 400 的實證就是核准前的狀態」。
>
> 下面兩套腳本：
> - **Plan A（live demo）**：未來 endpoint 解鎖後用（跨帳號讀取可行時）
> - **Plan B（本輪用）**：endpoint 鎖住時的 Architecture-Demo + 誠實揭露 400 錯誤

---

## Plan A｜Live Demo（endpoint 解鎖後用）

**Target permission**: `threads_profile_discovery`
**Video file**: `assets/app-review/profile_discovery.mp4`
**Duration target**: ≤ 90 seconds
**Language**: English UI + English voiceover

### 1. Use Case (one-liner)

> When the app owner finds an interesting public post on Threads, they paste its URL into the CLI to fetch the full text for their own later reading and study. The CLI returns the text to the owner's local terminal only — no republication.

### 2. Demo Step Table

| # | Action | CLI command | Expected terminal output (abbrev.) | Cross-validation |
|---|--------|-------------|-------------------------------------|-------------------|
| 0 | Title card (3s) | — | Architecture Note text slide | — |
| 1 | Show target post in Threads web | — (UI only) | — | Open `https://www.threads.com/@lin__photograph/post/<shortcode>` in browser; show the post text is public. |
| 2 | URL-first lookup | `threads profile lookup https://www.threads.com/@lin__photograph/post/<shortcode>` | `[OK] Post <post_id>` with text + permalink + timestamp | Split view with the browser from step 1: the `text` field from CLI matches the post text visible in Threads web. |
| 3 | JSON envelope | `threads profile lookup https://www.threads.com/@lin__photograph/post/<shortcode> --json` | `{"ok": true, "data": {"post": {"id": ..., "text": ..., "permalink": ..., "timestamp": ...}}}` | — |
| 4 | Browse author's recent posts | `threads profile posts lin__photograph --limit 5` | `[OK] 5 post(s):` listing id / timestamp / text preview for 5 recent public posts | Cut back to Threads web profile page for `@lin__photograph`; top 5 entries match the CLI output. |
| 5 | Closing value card (2s) | — | "URL → text → study." | — |

### 3. Voiceover Script (English)

1. "This application is a server-to-server CLI tool. Its purpose is to help the app owner study interesting posts by other Threads creators."
2. "Here is a public post on Threads that the owner wants to save for later reading."
3. "The CLI command `threads profile lookup` accepts the post URL. It returns the post text, permalink, and timestamp — all fields Meta has marked public in the Threads API."
4. "Cutting back to the browser, the text returned by the CLI matches the post exactly. The owner now has the content in a local terminal for their own study."
5. "Running with `--json` returns the same data as a structured envelope."
6. "The owner can also browse a creator's recent posts with `threads profile posts <username>` — useful when they want to learn from that creator's overall style."
7. "No content is republished or redistributed. The CLI only returns the post text to the owner's terminal, supporting their own learning workflow."

### 4. On-screen Captions & Tooltips

| Moment | Caption / tooltip text |
|--------|------------------------|
| Title card (0:00–0:03) | "Architecture Note: server-to-server CLI. Single-account, app-owner auth." |
| Step 1 browser cut | Label: "Public Threads post — URL is the only input the owner has." |
| Before step 2 command | "URL → fetch post text." |
| Step 2 output highlight | Draw connector from CLI `text:` line to the post text in the browser. |
| Before step 4 command | "Browse recent posts from a creator for systematic study." |
| Closing card | "`profile_discovery`: URL → text → study." |

### 5. Pre-recording Setup

- **Account**: App owner's Threads account, long-lived user access token exported as `THREADS_ACCESS_TOKEN`.
- **Terminal**: UTF-8 locale, font size 14pt.
- **Target post**: Pick one recent public post by `@lin__photograph` (or another public creator). Pre-open the URL in Threads web in a browser tab, ready to cut to.
- **Post-demo cleanup**: None. Read-only operation.

---

## Plan B｜Architecture-Demo with Honest Disclosure（本輪用）

**Target permission**: `threads_profile_discovery`
**Video file**: `assets/app-review/profile_discovery.mp4`
**Duration target**: ≤ 90 seconds
**Language**: English UI + English voiceover

**核心訊息**：CLI 與整合已實作、endpoint 定義明確於 Meta docs、use case 真實、核准後即可 live；pre-approval endpoint 回應 400 的實證納入影片。

**開頭必講（Title card，5s 內）**：
> "This app is a server-to-server CLI tool. The endpoint that `profile_discovery` unlocks is gated before approval, so this video demonstrates the implementation and the intended user journey rather than a live API response. The final step also shows the current pre-approval API behaviour for transparency."

### 1. Use Case (one-liner, 同 Plan A)

> When the app owner finds an interesting public post on Threads, they paste its URL into the CLI to fetch the full text for their own later reading and study. The CLI returns the text to the owner's local terminal only — no republication.

### 2. Plan B — Demo Step Table

| # | Action | On-screen content | Voiceover cue |
|---|--------|-------------------|---------------|
| 0 | Title card (5s) | Architecture Note + permission-lock disclosure (雙段文字) | "This app is a server-to-server CLI. The endpoint this permission unlocks is gated before approval, so this video demonstrates the implementation and the intended user journey instead of a live API success response." |
| 1 | Use case scene (10s) | Browser: open a public post on Threads, e.g. `https://www.threads.com/@lin__photograph/post/<shortcode>`; show the post text clearly readable | "The owner regularly finds interesting public posts on Threads and wants to save the full text for later study. Here is one such post — public, reachable by URL." |
| 2 | CLI help (10s) | Terminal: `threads profile --help`, then `threads profile lookup --help` — show `lookup <url>` and `posts <username>` sub-commands with `--limit` / `--cursor` / `--json` flags | "The CLI already implements a `profile` command group with two operations: `lookup` takes a post URL and returns the post text; `posts` lists a creator's recent public posts. Both will call the profile_discovery endpoint once approved." |
| 3 | Source code (15s) | Editor opens `threads_client.py`, highlight `resolve_post_by_url()` method: the URL parser (regex for `@username` + shortcode) and the GET call to `{THREADS_API_BASE}/{username}/threads`; also show `fetch_user_profile()` and `fetch_user_threads()` | "The client method implements URL parsing — extracting the `@username` and post shortcode — then queries the documented `/{username}/threads` endpoint, matching the post by its permalink shortcode. All target fields are the public ones Meta documents as reachable under `profile_discovery`." |
| 4 | Meta docs cross-check (10s) | Browser: Meta Threads API reference page for `/{threads-user-id}/threads` endpoint (public posts listing) | "This is the same endpoint documented in Meta's Threads API reference — confirming the permission and endpoint pair we are requesting." |
| 5 | Learning workflow (10s) | Editor: show a simple receiver pattern — e.g. terminal output piped into a local file or read by a notes app; emphasise "owner's own terminal, local only" | "The returned text goes only to the owner's local terminal — used by the owner to read and study other creators' work. No content is republished, redistributed, or shared with third parties." |
| 6 | Attempted live call + graceful failure (10s) | Terminal: run `threads profile lookup https://www.threads.com/@lin__photograph/post/<shortcode>`; show `[ERROR] HTTP 400: ... Object with ID 'lin__photograph' does not exist, cannot be loaded due to missing permissions` Then overlay text: "Endpoint unlocks upon approval" | "For transparency, the endpoint currently returns the documented pre-approval error — confirming the CLI is correctly wired and only the `profile_discovery` approval is outstanding." |
| 7 | Closing card (5s) | "`profile_discovery`: integration complete — awaiting endpoint activation." | — |

### 3. Plan B — Voiceover Script (English, line-by-line)

1. "This application is a server-to-server CLI tool. The endpoint unlocked by `profile_discovery` is permission-gated before approval, so this video shows the implementation and intended user journey, with the current pre-approval API response at the end."
2. "The owner regularly finds interesting public posts on Threads — like the one in this browser tab — and wants to save the text for their own later reading and study."
3. "The CLI exposes two sub-commands: `threads profile lookup <url>` to fetch a single post's text from its URL, and `threads profile posts <username>` to browse a creator's recent public posts."
4. "Looking at the source code: `resolve_post_by_url` parses the URL to extract the Threads `@username` and post shortcode, then queries the documented `/{username}/threads` endpoint to find the matching post."
5. "Meta's Threads API reference lists this endpoint and the field set we request — `id`, `text`, `permalink`, `timestamp`, `username` — all of them public on the platform."
6. "The returned text lands only in the owner's local terminal, used for their own study. No redistribution, no republication."
7. "Running the CLI against the live endpoint today returns the documented pre-approval error shown here — this confirms the CLI is wired correctly and is waiting on `profile_discovery` approval."
8. "Upon approval, the CLI will return the post text as described, supporting the owner's learning workflow."

### 4. Plan B — On-screen Captions & Tooltips

| Moment | Caption / tooltip text |
|--------|------------------------|
| Title card (0:00–0:05) | "Architecture Note: server-to-server CLI, app-owner auth. Endpoint permission-gated pre-approval; video demonstrates implementation + intent + pre-approval API behaviour." |
| Step 1 browser cut | "Public Threads post — reachable by URL. The only input the owner provides." |
| Step 2 CLI help | "Two sub-commands: `lookup <url>` (single post) + `posts <username>` (list recent)." |
| Step 3 source code | "URL parser + `/{username}/threads` GET. Fields = public metadata only." |
| Step 4 Meta docs | "Endpoint documented in Meta Threads API reference." |
| Step 5 learning workflow | "Text → owner's local terminal only. No republication." |
| Step 6 error overlay | "Endpoint unlocks upon `profile_discovery` approval." |
| Closing card | "`profile_discovery`: implementation shipped — awaiting approval." |

### 5. Plan B — Pre-recording Setup

- **Account**: App owner's Threads account, long-lived user access token exported as `THREADS_ACCESS_TOKEN`. Token is alive (`probe_profile_discovery.py` verifies `/me` returns 200).
- **Target URL**: Pick one recent public post by a real creator (e.g. `https://www.threads.com/@lin__photograph/post/<shortcode>`). Pre-open in Threads web. Verify post is public and reachable without login.
- **Editor**: VS Code (or similar) with `threads_client.py` and `threads_cli/profile.py` pinned as tabs, ready to scroll to `resolve_post_by_url`.
- **Browser**: Meta Threads API reference page for user threads listing endpoint bookmarked.
- **Terminal**: UTF-8 locale, 14pt font. Pre-run `threads profile --help` once to warm up the command parser cache.
- **Expected pre-approval error**: `[ERROR] HTTP 400: Object with ID '<username>' does not exist, cannot be loaded due to missing permissions, or does not support this operation`. **This is intentional — it is Step 6 of the demo.**
- **Disclosure Notes (送審時貼到 permission Notes 欄位)**:
  1. Full Architecture Note (server-to-server)
  2. Paragraph:
     > The endpoints unlocked by `threads_profile_discovery` — specifically `/{username}` and `/{username}/threads` — are not reachable prior to approval, including for the app owner's own username. The attached video demonstrates: (a) the learning use case in the Threads client, (b) the already-shipped CLI `threads profile lookup` and `threads profile posts` with their source code targeting the documented endpoints, (c) the read-only single-user learning workflow (text lands in owner's local terminal, not republished), and (d) the current pre-approval API response (HTTP 400) as evidence the CLI is wired and awaiting activation.
  3. Link to CLI source code in the repo (if public) or attached as PDF.
- **Post-demo cleanup**: None. Read-only operation.

---

## 附錄 A｜CLI 介面最小定義（供實作對齊）

本輪實作只覆蓋 **Plan B 展示所需的指令**，`threads profile get` 不實作。

| CLI 指令 | client method | endpoint | 註 |
|---|---|---|---|
| `threads profile lookup <url>` | `resolve_post_by_url(url, token)` | 內部呼叫 `fetch_user_threads`；URL → parsed user + shortcode → list posts → match by permalink | **旗艦指令**，Plan B Step 2/6 用 |
| `threads profile posts <username> [--limit N] [--cursor C]` | `fetch_user_threads(username, token, ...)` | `GET /{username}/threads` | Plan B Step 3 用作代碼走讀素材 |

**URL 格式支援**：
- ✅ `https://www.threads.com/@{username}/post/{shortcode}` — 主要支援
- ❌ `https://www.threads.com/t/{shortcode}` — 短格式缺 username，無法透過 profile_discovery 解析，應回 `UNSUPPORTED_URL` 錯誤碼

**錯誤碼對應**：

| 情境 | 錯誤碼 | 訊息範例 |
|---|---|---|
| URL 格式不符 | `UNSUPPORTED_URL` | "URL must be in form `https://www.threads.com/@username/post/shortcode`" |
| HTTP 400 + "does not exist" | `PERMISSION_REQUIRED` | "Threads profile_discovery permission is required to access this endpoint" |
| 其他 HTTP 4xx/5xx | `API_ERROR` | "Threads API error: ..." |
| 網路錯誤 | `API_ERROR` | "Threads API error: ..." |
| URL shortcode 在 user threads 列表中找不到 | `POST_NOT_FOUND` | "Post shortcode `{shortcode}` not found in `{username}`'s recent posts" |
