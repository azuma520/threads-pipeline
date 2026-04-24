# Demo Script — `threads_manage_mentions`

> ⏸️ **Deferred — 本輪不送**
>
> 診斷結果（2026-04-23）：`/me/threads_mentions` 在 `manage_mentions` 核准前完全鎖住，實測 Graph API 回 `Tried accessing nonexisting field (threads_mentions)` / HTTP 500（三次重試皆同）。意味著無法錄出 live API 成功的 demo——硬送重蹈「demo 不完整」覆轍。
>
> 決策：本輪送 4 個（content_publish / keyword_search / manage_replies / read_replies），`manage_mentions` 延到**下一輪單送**。
>
> 下面是兩套腳本：
> - **Plan A（live demo）**：此 endpoint 未來解鎖後用，格式與其他 4 份腳本一致
> - **Plan B（Architecture-Demo）**：若下輪單送時 endpoint 仍鎖住，用這套「CLI 實作 + 原始碼 + Meta docs + Threads UI」的組合影片代替 live API demo

---

## Plan A｜Live Demo（endpoint 解鎖後用）

**Target permission**: `threads_manage_mentions`
**Video file**: `assets/app-review/manage_mentions.mp4`
**Duration target**: ≤ 2 minutes
**Language**: English UI + English voiceover

---

## 1. Use Case (one-liner)

> This CLI lists recent @-mentions of the app owner's Threads account so the advisor pipeline can triage incoming mentions and decide which ones the owner should acknowledge or follow up on.

---

## 2. Demo Step Table

| # | Action | CLI command | Expected terminal output (abbrev.) | Cross-validation in Threads app |
|---|--------|-------------|-------------------------------------|----------------------------------|
| 0 | Show Architecture Note title card (3s) | — | Static text slide | — |
| 1 | Show mentions in Threads app | — (UI only) | — | Open the Threads app → Activity / Notifications → Mentions tab. Show at least two recent @-mentions of the app owner's account. |
| 2 | Human-readable mention listing | `threads account mentions --limit 10` | `[OK] 2 mention(s): <mention_id_1>  @user1  <preview...> <mention_id_2>  @user2  <preview...>` | Split view or cut back to the Threads app: each mention line in the CLI matches one of the entries on the Mentions tab — same @-handle, same text. |
| 3 | JSON envelope for programmatic consumption | `threads account mentions --limit 10 --json` | JSON envelope: `{"ok": true, "data": {"mentions": [{"id": ..., "username": ..., "text": ...}, ...]}, "warnings": [], "next_cursor": null}` | — |
| 4 | Closing value card (2s) | — | "Mentions → triage → respond." | — |

---

## 3. Voiceover Script (English, line-by-line)

1. "This application is a server-to-server CLI tool. Mention management is how the advisor pipeline triages incoming @-mentions on the app owner's account."
2. "Here is the Mentions tab in the Threads app, showing two recent @-mentions of my account."
3. "I run `threads account mentions` with a result limit of ten. The CLI calls the mentions endpoint and prints each mention's ID, author handle, and text preview."
4. "Cutting back to the Threads app, each mention line from the CLI lines up with the entries on the Mentions tab — same authors, same text, same order."
5. "Re-running with `--json` returns the same data as a structured envelope. The advisor pipeline consumes this to prioritise which mentions warrant a response."
6. "This is how the mentions endpoint is exercised end to end by our pipeline."

---

## 4. On-screen Captions & Tooltips

| Moment | Caption / tooltip text |
|--------|------------------------|
| Title card (0:00–0:03) | "Architecture Note: server-to-server CLI. Single-account, app-owner auth." |
| Step 1 Threads app cut | Label: "Threads app — Activity → Mentions tab (2 recent mentions)." |
| Before step 2 command | "List @-mentions with human-readable output." |
| Step 2 output highlight | Draw connector lines from each CLI mention to the corresponding entry on the Mentions tab. |
| Before step 3 command | "`--json` returns the same data as a structured envelope." |
| Step 3 output highlight | Box the `data.mentions[]` array. |
| Closing card | "`manage_mentions`: triage incoming conversations." |

---

## 5. Pre-recording Setup

- **Account**: App owner's Threads account, authenticated via long-lived user access token exported as `THREADS_ACCESS_TOKEN`.
- **Terminal**: UTF-8 locale. Font size bumped to 14pt for legibility.
- **Pre-existing state**:
  - The app owner's account must have at least **two recent @-mentions** on the Mentions tab. If not, arrange ahead of filming: have a second test account publish two posts that @-mention the owner. Wait ~5 minutes for the mentions to propagate before recording.
  - These mentions must be visible on the Mentions tab in the Threads client — otherwise the cross-validation in step 2 will fail.
- **Threads client**: Threads web (`threads.net`) logged into the app-owner account, Activity → Mentions tab open in a tab, ready to cut to.
- **Post-demo cleanup**: None. Read-only operation.

---

## Plan B｜Architecture-Demo（endpoint 仍鎖住時用）

**用途**：若下輪單送時 `/me/threads_mentions` 仍 permission-locked，用此影片代替 live demo。
**核心訊息**：「CLI 與整合已實作、endpoint 在 Meta docs 內定義明確、use case 場景真實存在——核准後即可 live」。
**開頭必講**：在影片開頭 5 秒內清楚告知審查員「此 permission 所屬 endpoint 需先核准方能呼叫，本影片展示 CLI 實作與預期 use case」。

### Plan B — Demo Step Table

| # | Action | On-screen content | Voiceover cue |
|---|--------|-------------------|---------------|
| 0 | Title card (5s) | "Architecture Note + permission-lock disclosure" 雙段文字 | "This app is a server-to-server CLI. The endpoint this permission unlocks is gated before approval, so this video demonstrates the implementation and the intended user journey instead of a live API response." |
| 1 | Use case scene (10s) | Threads app → Activity → Mentions tab with ≥ 2 真實 @mentions of owner | "In practice the app owner receives @-mentions from the community, visible here in the Threads app. Triaging these is the workflow we want to automate." |
| 2 | CLI help (10s) | Terminal: `threads account mentions --help` — show options `--limit` / `--cursor` / `--json` | "The CLI already implements a `mentions` subcommand that will call the endpoint once approved. Help output lists pagination and machine-readable output flags." |
| 3 | Source code (15s) | Editor opens `threads_client.py` around `list_mentions()`; highlight `url = f"{THREADS_API_BASE}/me/threads_mentions"` + `fields=_DEFAULT_MENTION_FIELDS` | "The client method is implemented and targets the documented `/me/threads_mentions` endpoint, returning id, text, username, timestamp, and permalink." |
| 4 | Meta docs cross-check (10s) | Browser: Meta Threads API reference page for `/me/threads_mentions` | "This is the same endpoint as documented in Meta's Threads API reference — confirming the permission and endpoint pair we are requesting." |
| 5 | Advisor pipeline integration (15s) | Editor: show where mentions output feeds into the advisor pipeline (or point at the CLI `--json` envelope structure); side-by-side with the Mentions tab from step 1 | "Once approved, the CLI's JSON envelope feeds directly into our advisor pipeline, which classifies which mentions deserve the owner's follow-up — turning the manual triage from step 1 into an automated workflow." |
| 6 | Attempted live call + graceful failure (10s) | Terminal: run `threads account mentions`; show `[ERROR] Threads API error: 500 ... nonexisting field (threads_mentions)`. Then overlay text "Endpoint unlocks upon approval" | "For transparency, the endpoint currently responds with the pre-approval error — confirming that the CLI is correctly wired and only the approval is outstanding." |
| 7 | Closing card (5s) | "`manage_mentions`: integration complete — awaiting endpoint activation." | — |

### Plan B — Pre-recording Setup

- **Account**: App owner's Threads account, with ≥ 2 real @-mentions already visible on the Activity → Mentions tab (same as Plan A).
- **Editor**: VS Code (or similar) with `threads_client.py` and the advisor pipeline integration file both pinned as tabs.
- **Browser**: Meta Threads API reference page for `/me/threads_mentions` bookmarked and pre-loaded.
- **Terminal**: Ready to run `threads account mentions --help` and `threads account mentions`. Expect the second call to fail with the `nonexisting field` error — this is intentional and part of the demo (it proves the CLI is wired correctly, only the approval is pending).
- **Disclosure Notes**: When submitting, include in the permission's Notes field:
  1. Full Architecture Note (server-to-server)
  2. The paragraph: "This permission's endpoint `/me/threads_mentions` is not reachable prior to approval. The attached video demonstrates: (a) the use case in the Threads client, (b) the already-shipped CLI and source code targeting the documented endpoint, (c) the pipeline integration, and (d) the current pre-approval API response as evidence that the integration is wired and awaiting activation."
  3. Link to the CLI source code in the repo (if repo is public) or attached as a PDF.
- **Optional safety net**: Open a Meta Developer Support ticket ahead of resubmission asking their preferred demo format for permission-locked endpoints — paste their reply into the Notes.
