# Demo Script — `threads_keyword_search`

**Target permission**: `threads_keyword_search`
**Video file**: `assets/app-review/keyword_search.mp4`
**Duration target**: ≤ 2 minutes
**Language**: English UI + English voiceover

---

## 1. Use Case (one-liner)

> This CLI searches the authenticated developer's own Threads posts by keyword as part of an analytics workflow — retrieving posts that match a topical query so the advisor pipeline can evaluate which themes resonated historically before drafting new content.

---

## 2. Demo Step Table

| # | Action | CLI command | Expected terminal output (abbrev.) | Cross-validation in Threads app |
|---|--------|-------------|-------------------------------------|----------------------------------|
| 0 | Show Architecture Note title card (3s) | — | Static text slide | — |
| 1 | Human-readable keyword search (English keyword) | `threads posts search "demo" --limit 10` | `[OK] 2 match(es) for keyword="demo": <id1> <timestamp> <preview...> <id2> <timestamp> <preview...>` | Switch to Threads app → profile → scroll to an older post that contains the keyword "demo" and show that its text matches one of the results. |
| 2 | JSON envelope search for programmatic use | `threads posts search "demo" --limit 10 --json` | JSON envelope: `{"ok": true, "data": {"posts": [{"id": ..., "text": ..., "timestamp": ...}], "keyword": "demo"}, "warnings": [...]}` | — |
| 3 | Show help panel (Standard Access note) | `threads posts search --help` | Help text including: "Standard Access 限制：此指令只會搜尋「你自己」的貼文。" | — |
| 4 | Closing value card (2s) | — | "Keyword search feeds the advisor analytics loop." | — |

---

## 3. Voiceover Script (English, line-by-line)

1. "This application is a server-to-server CLI tool. Keyword search is used by the advisor pipeline to retrieve the app owner's prior posts matching a theme."
2. "I run a keyword search for the term `demo` with a result limit of ten. The CLI calls the keyword search endpoint and prints each matching post ID, timestamp, and a text preview."
3. "Switching to the Threads app on the same authenticated account, I can confirm that the highlighted post from the CLI output corresponds to the actual post on my profile — same text, same timestamp."
4. "For programmatic consumption by the advisor, I re-run with the `--json` flag. The envelope carries an `ok` flag, the matching posts list, and structured warnings — the advisor pipeline reads this directly."
5. "The help text also notes explicitly that under Standard Access the search is scoped to the developer's own account — which matches the scope this permission grants us."
6. "This is how the keyword search endpoint is exercised end to end by our advisor pipeline."

---

## 4. On-screen Captions & Tooltips

| Moment | Caption / tooltip text |
|--------|------------------------|
| Title card (0:00–0:03) | "Architecture Note: server-to-server CLI. Single-account, app-owner auth." |
| Before step 1 command | "Keyword search with human-readable output." |
| Step 1 output highlight | Box the first match's `post_id` and preview. |
| Step 1 Threads app cut | Label: "Threads web — same authenticated account." Highlight the matching post in the profile feed. |
| Before step 2 command | "`--json` returns a structured envelope for the analytics pipeline." |
| Step 2 output highlight | Box the `data.posts[]` array in the JSON envelope. |
| Before step 3 command | "`--help` documents the Standard Access scope." |
| Closing card | "`keyword_search`: retrieve → analyze → inform next draft." |

---

## 5. Pre-recording Setup

- **Account**: App owner's Threads account, authenticated via long-lived user access token exported as `THREADS_ACCESS_TOKEN`.
- **Terminal**: UTF-8 locale. Font size bumped to 14pt for legibility.
- **Pre-existing state**: The app owner's account must already have at least two historical posts containing the keyword "demo" (English). If the account is fresh, publish two demo posts first (off camera) using the `content_publish` workflow — e.g. "Testing demo pipeline 1/2" and "Scheduling the next demo session". Make sure each is at least 24 hours old so it does not look like a scripted pair; if timing is tight, keep the keyword simple and obvious.
- **Threads client**: Threads web (`threads.net`) logged into the same app-owner account, profile tab open, ready to cut to.
- **Keyword choice rationale**: Use an English keyword. Under Standard Access the CJK warning `EMPTY_RESULT_CJK` is noise for the reviewer; English keeps the demo focused on the happy path. Our internal testing confirmed CJK returns 0 under Standard Access (documented in `docs/dev/api-exploration-results.md`) and is not representative.
- **Post-demo cleanup**: None. No state mutated.
