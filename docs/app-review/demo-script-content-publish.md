# Demo Script — `threads_content_publish`

**Target permission**: `threads_content_publish`
**Video file**: `assets/app-review/content_publish.mp4`
**Duration target**: ≤ 2 minutes
**Language**: English UI + English voiceover

---

## 1. Use Case (one-liner)

> This CLI lets the app owner publish a single post or a multi-post thread chain to their own Threads account directly from a terminal, as part of an authoring workflow that prepares and publishes drafts reviewed by our internal advisor tool.

---

## 2. Demo Step Table

| # | Action | CLI command | Expected terminal output (abbrev.) | Cross-validation in Threads app |
|---|--------|-------------|-------------------------------------|----------------------------------|
| 0 | Show Architecture Note title card (3s) | — | Static text slide | — |
| 1 | Dry-run a single post | `threads post publish "Hello from the CLI — demo post for Meta App Review."` | `[DRY RUN] Would publish: ... Character count: 55 ... Add --confirm to actually publish.` | — |
| 2 | Actually publish the single post | `threads post publish "Hello from the CLI — demo post for Meta App Review." --confirm --yes` | `[OK] Published as post <post_id>` | Switch to Threads web/app on the same logged-in account. Refresh profile feed. Show the post appearing at top with matching text. |
| 3 | Dry-run a chain from a draft file | `threads post publish-chain drafts/smoke-test.txt` | `[DRY RUN] Would publish chain of 3 posts: ... 1/3 (opener): ... 2/3 (reply): ... 3/3 (reply): ... Total: 3 posts, N chars ... Add --confirm to actually publish.` | — |
| 4 | Actually publish the chain | `threads post publish-chain drafts/smoke-test.txt --confirm --yes` | `[OK] Published chain of 3 posts: 1. <id1> 2. <id2> 3. <id3>` | Switch back to Threads app. Show the opener post, tap it to reveal the two sequential replies forming the chain. |
| 5 | Closing value card (2s) | — | "From terminal to Threads in one command." | — |

---

## 3. Voiceover Script (English, line-by-line)

1. "This application is a server-to-server CLI tool used by a single developer to author and publish content to their own Threads account."
2. "First, I run a dry-run publish. The tool previews the text and character count but does not call the Threads API."
3. "Now I re-run with `--confirm --yes`. The CLI calls the content publishing endpoint and returns the new post ID."
4. "Switching to the Threads app on the same authenticated account, the post appears at the top of my profile feed."
5. "Next, a thread chain. The draft file contains three blocks separated by blank lines — one opener and two follow-up replies."
6. "Dry-run first — the tool shows the parsed chain and expected order."
7. "Confirming the publish — the CLI returns the three post IDs in order."
8. "Back in the Threads app, tapping the opener reveals the two subsequent replies wired into the same chain."
9. "This is the content publishing flow as used by our internal authoring pipeline."

---

## 4. On-screen Captions & Tooltips

| Moment | Caption / tooltip text |
|--------|------------------------|
| Title card (0:00–0:03) | "Architecture Note: server-to-server CLI. Single-account, app-owner auth." |
| Before step 1 command | "Dry-run: preview without calling the API." |
| Step 2 output highlight | Box the `[OK] Published as post <id>` line. |
| Step 2 Threads app cut | Label: "Threads web — same authenticated account." |
| Before step 3 command | "`publish-chain`: publishes a multi-post thread from a draft file." |
| Step 4 output highlight | Box the three-line list of post IDs. |
| Step 4 Threads app cut | Label: "Thread chain visible in Threads app." |
| Closing card | "`content_publish`: author → CLI → Threads." |

---

## 5. Pre-recording Setup

- **Account**: App owner's Threads account, already authenticated with a long-lived user access token exported as `THREADS_ACCESS_TOKEN`.
- **Terminal**: UTF-8 locale. Font size bumped to 14pt for legibility.
- **Draft file**: `drafts/smoke-test.txt` containing three paragraphs separated by blank lines. Keep each paragraph short (< 300 chars) and recognisable so the cross-validation in the Threads app is unambiguous.
- **Threads client**: Threads web (`threads.net`) logged into the same app-owner account, on the second browser window ready to cut to.
- **Pre-existing state**: None required. The demo creates new posts.
- **Post-demo cleanup** (optional, not on camera): Delete the four posts via `threads post delete <id> --confirm --yes` if you don't want to keep the demo posts on the live profile.
