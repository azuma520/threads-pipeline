# Demo Script — `threads_read_replies`

**Target permission**: `threads_read_replies`
**Video file**: `assets/app-review/read_replies.mp4`
**Duration target**: ≤ 2 minutes
**Language**: English UI + English voiceover

---

## 1. Use Case (one-liner)

> This CLI fetches the replies underneath a specific post on the app owner's Threads account so the advisor pipeline can summarise community sentiment and surface questions the owner should follow up on.

---

## 2. Demo Step Table

| # | Action | CLI command | Expected terminal output (abbrev.) | Cross-validation in Threads app |
|---|--------|-------------|-------------------------------------|----------------------------------|
| 0 | Show Architecture Note title card (3s) | — | Static text slide | — |
| 1 | Show the target post in Threads app | — (UI only) | — | Open the target post in the Threads app. Show reply count badge at the bottom (e.g. "3 replies"). |
| 2 | Human-readable reply listing | `threads post replies <POST_ID> --limit 10` | `[OK] 3 reply(s) for post <POST_ID>: <reply_id_1>  @user1  <preview...> <reply_id_2>  @user2  <preview...> <reply_id_3>  @user3  <preview...>` | Split view or cut back to the Threads app: show each reply's author @-handle and text matching the CLI output line-by-line. |
| 3 | JSON envelope for programmatic consumption | `threads post replies <POST_ID> --limit 10 --json` | JSON envelope: `{"ok": true, "data": {"replies": [{"id": ..., "username": ..., "text": ...}, ...]}, "warnings": [], "next_cursor": null}` | — |
| 4 | Closing value card (2s) | — | "Replies feed sentiment and follow-up triage." | — |

---

## 3. Voiceover Script (English, line-by-line)

1. "This application is a server-to-server CLI tool. Reading replies is how the advisor pipeline monitors the community response on the app owner's posts."
2. "Here is a post on my Threads profile with three replies visible under it."
3. "I run `threads post replies` with that post's ID. The CLI calls the read replies endpoint and prints each reply's ID, author handle, and text preview."
4. "Cutting back to the Threads app, each reply shown by the CLI matches the replies underneath the post, in the same order — IDs, authors, and text all align."
5. "Re-running with `--json` returns a structured envelope. The advisor pipeline consumes this format to analyse sentiment and pick replies that deserve a human follow-up."
6. "This is how the read replies endpoint is exercised end to end by our pipeline."

---

## 4. On-screen Captions & Tooltips

| Moment | Caption / tooltip text |
|--------|------------------------|
| Title card (0:00–0:03) | "Architecture Note: server-to-server CLI. Single-account, app-owner auth." |
| Step 1 Threads app cut | Label: "Threads web — target post, reply count = 3." |
| Before step 2 command | "Fetch replies by post ID (human-readable output)." |
| Step 2 output highlight | Draw connector lines from CLI reply IDs to the corresponding replies in the Threads app. |
| Before step 3 command | "`--json` returns the same data as a structured envelope." |
| Step 3 output highlight | Box the `data.replies[]` array. |
| Closing card | "`read_replies`: fetch → analyze → follow up." |

---

## 5. Pre-recording Setup

- **Account**: App owner's Threads account, authenticated via long-lived user access token exported as `THREADS_ACCESS_TOKEN`.
- **Terminal**: UTF-8 locale. Font size bumped to 14pt for legibility.
- **Pre-existing state**:
  - At least one post on the owner's profile that already has **three real replies** visible.
  - If no such post exists, ahead of filming: use a second test account (or ask a friend) to leave three replies on a chosen owner post. Do not leave replies from the same app-owner account, as the purpose is to show community replies being surfaced.
  - Record the target post's ID in advance (e.g. via `threads posts list --limit 5`) so the demo does not have to look it up on camera.
- **Threads client**: Threads web (`threads.net`) logged into the app-owner account, with the target post already open in a tab ready to cut to.
- **Post-demo cleanup**: None. Read-only operation.
