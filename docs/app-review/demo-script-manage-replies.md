# Demo Script — `threads_manage_replies`

**Target permission**: `threads_manage_replies`
**Video file**: `assets/app-review/manage_replies.mp4`
**Duration target**: ≤ 2 minutes
**Language**: English UI + English voiceover

---

## 1. Use Case (one-liner)

> This CLI lets the app owner respond to replies under their posts and moderate unwanted replies — adding a new reply, hiding an off-topic reply, and un-hiding if the moderation was wrong — as part of a moderation workflow assisted by the advisor pipeline.

---

## 2. Demo Step Table

| # | Action | CLI command | Expected terminal output (abbrev.) | Cross-validation in Threads app |
|---|--------|-------------|-------------------------------------|----------------------------------|
| 0 | Show Architecture Note title card (3s) | — | Static text slide | — |
| 1 | Show the target post and its replies | — (UI only) | — | Open the target post in the Threads app. Expand the reply thread and show the self-reply (by the app owner) that we will moderate later — its content is a broken-encoding test reply, making it a safe, no-impact moderation target. |
| 2 | Dry-run adding a reply | `threads reply add <POST_ID> "Thanks for the feedback — will follow up shortly."` | `[DRY RUN] Would reply to post <POST_ID>: ... Character count: 51 ... Add --confirm to actually reply.` | — |
| 3 | Actually add the reply | `threads reply add <POST_ID> "Thanks for the feedback — will follow up shortly." --confirm --yes` | `[OK] Reply posted as <NEW_REPLY_ID> (parent: <POST_ID>)` | Cut to the Threads app. Refresh the post. The new reply appears under the post, authored by the app owner. |
| 4 | Hide an existing reply (owner's own test self-reply; same flow applies to community replies) | `threads reply hide <EXISTING_REPLY_ID>` | `[OK] Hidden reply <EXISTING_REPLY_ID>` | Cut to the Threads app. The hidden reply is now collapsed or labelled "Hidden" under the post. |
| 5 | Un-hide the same reply | `threads reply unhide <EXISTING_REPLY_ID>` | `[OK] Unhidden reply <EXISTING_REPLY_ID>` | Cut to the Threads app. The reply is visible again as before. |
| 6 | Closing value card (2s) | — | "Add · hide · unhide — full reply management." | — |

---

## 3. Voiceover Script (English, line-by-line)

1. "This application is a server-to-server CLI tool. Reply management covers three actions: adding a reply, hiding a reply, and un-hiding a reply."
2. "Here is a target post on the app owner's profile. Below it, among several replies, is a broken-encoding test reply the owner previously posted on their own post — that will be our moderation target, chosen so this demonstration has no impact on any community member."
3. "First, I dry-run adding a new reply. The CLI previews the text and character count without calling the API."
4. "Re-running with `--confirm --yes` actually calls the content publishing endpoint to reply. The CLI returns the new reply ID."
5. "Back in the Threads app, refreshing the post shows the new reply authored by the app-owner account."
6. "Next, I hide that earlier broken-encoding reply using `threads reply hide` and its reply ID. In production, the same flow is used to moderate community replies — here I'm moderating my own test reply to avoid affecting any community member."
7. "In the Threads app, the hidden reply is now collapsed and marked as hidden under the post — moderation succeeded."
8. "To demonstrate reversibility, I run `threads reply unhide` with the same reply ID. The reply becomes visible again."
9. "This is the full manage-replies lifecycle — add, hide, unhide — as driven by the app owner's CLI."

---

## 4. On-screen Captions & Tooltips

| Moment | Caption / tooltip text |
|--------|------------------------|
| Title card (0:00–0:03) | "Architecture Note: server-to-server CLI. Single-account, app-owner auth." |
| Step 1 Threads app cut | Label: "Target post — existing broken-encoding self-reply (moderation target, no third-party impact)." |
| Before step 2 command | "Dry-run: preview the reply text without calling the API." |
| Before step 3 command | "Confirm: the CLI publishes the reply." |
| Step 3 Threads app cut | Highlight the newly added reply under the post. |
| Before step 4 command | "Hide a reply by reply ID." |
| Step 4 Threads app cut | Highlight the reply collapsed / marked hidden. |
| Before step 5 command | "Unhide reverses the action." |
| Step 5 Threads app cut | Highlight the reply re-appearing in normal view. |
| Closing card | "`manage_replies`: add · hide · unhide." |

---

## 5. Pre-recording Setup

- **Account**: App owner's Threads account, authenticated via long-lived user access token exported as `THREADS_ACCESS_TOKEN`.
- **Terminal**: UTF-8 locale. Font size bumped to 14pt for legibility.
- **Pre-existing state**:
  - A post on the owner's profile that already has at least **one existing self-reply by the owner that is safe to hide** (a broken-encoding test reply, an obsolete note, etc.). Using a self-reply as the moderation target is intentional — it keeps the demo zero-impact on any community member while still exercising the exact same `/hide` + `/unhide` API endpoints that production moderation of community replies uses.
  - Record in advance: the target **post ID** (for step 3) and the **self-reply ID to moderate** (for steps 4 and 5). Fetch the reply ID via `threads post replies <POST_ID>` before filming.
- **Threads client**: Threads web (`threads.net`) logged into the app-owner account, target post open in a tab, ready to refresh and cut to after each CLI action.
- **Post-demo cleanup**:
  - Step 5 already un-hides the moderation action, so no hidden state is left behind.
  - Optionally delete the reply from step 3 via `threads post delete <NEW_REPLY_ID> --confirm --yes` to avoid leaving the demo reply on the live post.
