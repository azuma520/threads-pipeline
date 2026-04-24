# Submission Notes — 2026-04-24 重送（3 個 permission）

**用途**：送審時逐欄複製到 Meta Developer Dashboard 的 "Notes for reviewer" 欄位。
**語言**：全英文（Meta reviewer 閱讀語言）。
**結構**：每個 permission 一段獨立 Notes，共用 Architecture Note。

---

## 共用前言 — Architecture Note

> This application is a server-to-server CLI tool used for single-account
> content analytics and authoring workflows. It authenticates via a long-lived
> user access token obtained once by the developer (app owner). There is no
> end-user frontend, no OAuth flow triggered by third parties, and no System
> User token.
>
> In accordance with the App Review guidance — "if your application is a
> server-to-server application or uses system-user tokens to access Meta APIs,
> please note this in your next submission so we understand why no front-end
> Meta Login flow is visible" — we explicitly state this here. The absence of
> the Meta Login UI in the attached screen recording is expected and not a
> defect of the demonstration. The authenticated user shown in the video is
> the app owner / developer, operating the CLI on their own Threads account.
>
> All operations demonstrated (searching, reading replies, reading public
> profiles) are executed by the CLI as the authenticated developer account.
> Each recording shows (1) the CLI invocation, (2) the API response, and,
> where applicable, (3) cross-validation in the native Threads client on the
> same account.

---

## Permission 1 — `threads_keyword_search`

**Video file**: `keyword_search.mp4`

**Use Case (one-liner)**:
> This CLI searches the authenticated developer's own Threads posts by
> keyword as part of an analytics workflow — retrieving posts that match a
> topical query so the advisor pipeline can evaluate which themes resonated
> historically before drafting new content.

**Demo coverage**: The video shows (a) a human-readable keyword search
(`threads posts search "API" --limit 10`) producing matching owner posts
with IDs, timestamps, and text previews, (b) the same query with `--json`
returning a structured envelope that the advisor pipeline consumes
programmatically, and (c) cross-validation in Threads web on the same
app-owner account where one of the matched posts is located in the profile
feed and the text is shown to match the CLI output verbatim.

**Notes for reviewer (paste)**:

```
[Architecture Note]
<paste the Architecture Note block above>

[Use case]
<paste the one-liner above>

[What the video shows]
1. `threads posts search "API" --limit 10` — human-readable output, 10+ matches
   against the app owner's own posts.
2. `threads posts search "API" --limit 10 --json` — JSON envelope
   ({ok, data.posts, data.keyword, warnings}) consumed by the advisor
   analytics pipeline.
3. `threads posts search --help` — CLI documents the Standard Access scope
   (searches only the authenticated user's posts) so the Advanced scope
   requested here is clear: it unlocks cross-account search and non-ASCII
   keyword support, which Standard Access does not provide.

The video is English UI + English voiceover, ≤ 2 minutes, 1080p.
```

---

## Permission 2 — `threads_read_replies`

**Video file**: `read_replies.mp4`

**Use Case (one-liner)**:
> This CLI fetches the replies underneath a specific post on the app owner's
> Threads account so the advisor pipeline can summarise community sentiment
> and surface questions the owner should follow up on.

**Demo coverage**: The video shows (a) the target post open in Threads web
with its reply count visible, (b) `threads post replies <post_id> --limit 10`
producing the replies with author handles and text previews that align
line-by-line with the replies shown in the Threads client, and (c) the same
command with `--json` returning a structured envelope used by the advisor
pipeline for sentiment analysis and follow-up triage.

**Notes for reviewer (paste)**:

```
[Architecture Note]
<paste the Architecture Note block above>

[Use case]
<paste the one-liner above>

[What the video shows]
1. Threads web — target post on the app owner's account with reply count
   visible.
2. `threads post replies <post_id> --limit 10` — human-readable list of
   replies with IDs, author handles, and text previews.
3. Cross-validation: each reply in the CLI output matches a reply underneath
   the post in Threads web, in the same order.
4. `threads post replies <post_id> --limit 10 --json` — structured envelope
   ({ok, data.replies, next_cursor}) consumed by the advisor pipeline for
   sentiment analysis and follow-up selection.

The video is English UI + English voiceover, ≤ 2 minutes, 1080p.
```

---

## Permission 3 — `threads_profile_discovery`

**Video file**: `profile_discovery.mp4` (Plan B — Architecture-Demo with
honest disclosure of pre-approval endpoint state)

**Use Case (one-liner)**:
> When the app owner finds an interesting public post on Threads, they paste
> its URL into the CLI to fetch the full post text for their own later
> reading and study. The CLI returns the text to the owner's local terminal
> only — no republication or redistribution.

**Demo coverage**: The endpoints unlocked by `threads_profile_discovery` —
`/{username}` and `/{username}/threads` — are not reachable prior to
approval, including for the app owner's own username (verified:
`probe_profile_discovery.py` returns HTTP 400 "Object with ID '<username>'
does not exist, cannot be loaded due to missing permissions"). The attached
video therefore follows an Architecture-Demo structure with honest disclosure:
(a) the learning use case shown in the Threads client, (b) the CLI commands
`threads profile lookup <url>` and `threads profile posts <username>`
already implemented and targeting the documented endpoints, (c) the source
code of `resolve_post_by_url()` parsing the URL and calling the documented
`/{username}/threads` endpoint, (d) the public field set requested (`id`,
`text`, `permalink`, `timestamp`, `username`) cross-referenced with the Meta
Threads API documentation, (e) the read-only single-user learning workflow
(text lands only in the owner's local terminal; no republication), and (f)
the current pre-approval API response (HTTP 400) as explicit evidence that
the CLI is wired correctly and only the `profile_discovery` approval is
outstanding.

**Notes for reviewer (paste)**:

```
[Architecture Note]
<paste the Architecture Note block above>

[Use case]
<paste the one-liner above>

[Endpoint pre-approval state — transparent disclosure]
The endpoints unlocked by `threads_profile_discovery` — `/{username}` and
`/{username}/threads` — are not reachable prior to approval. This applies
even to the app owner's own username. The attached video is therefore
structured as an implementation-and-intent demo, with the current HTTP 400
pre-approval response captured as Step 6 to show the CLI is correctly wired
and awaiting endpoint activation, not misconfigured.

[What the video shows]
1. Title card — Architecture Note + endpoint-lock disclosure (≈5s).
2. Use case scene — a public post on Threads in the browser; this is what
   the owner wants to save the text of for later reading.
3. CLI help panel — `threads profile lookup <url>` and `threads profile
   posts <username>`, with `--limit`, `--cursor`, `--json` flags.
4. Source code — `threads_client.py` `resolve_post_by_url()`: regex URL
   parser (extracting `@username` and post shortcode) plus the GET call to
   the documented `/{username}/threads` endpoint; requested fields are the
   public ones Meta documents under `profile_discovery`.
5. Meta API docs — browser tab showing the Meta Threads API reference for
   the user-threads listing endpoint, confirming the permission / endpoint
   pair.
6. Learning workflow — the returned text is piped only to the owner's local
   terminal for the owner's own study; no republication or redistribution.
7. Attempted live call — `threads profile lookup <public-post-url>` returns
   the documented pre-approval error:
   `HTTP 400: Unsupported get request. Object with ID '<username>' does not
   exist, cannot be loaded due to missing permissions, or does not support
   this operation`
   — this is the expected pre-approval state, captured deliberately.
8. Closing card — "`profile_discovery`: integration complete — awaiting
   endpoint activation."

The video is English UI + English voiceover, ≤ 90 seconds, 1080p.

[Why we are submitting despite the endpoint being pre-approval locked]
The CLI integration, URL parsing, endpoint targeting, field selection, and
error handling are all implemented against the documented Meta Threads API
surface. We confirmed via direct HTTP probing (`scripts/probe_profile_
discovery.py`, stored in the project repository) that the endpoint consistently
returns HTTP 400 prior to approval for any username — this is a platform
gate, not a CLI defect. Granting this permission will enable the
already-shipped commands to begin returning real data to the owner's
learning workflow.
```

---

## 4. 送審前最終檢查

- [ ] 3 部影片檔已在 `assets/app-review/`（`keyword_search.mp4` / `read_replies.mp4` / `profile_discovery.mp4`）
- [ ] 每個 permission 上傳對應影片
- [ ] 每個 permission 的 Notes 欄位貼入上述 `[Architecture Note] ... [What the video shows]` 區塊
- [ ] `profile_discovery` 多貼 `[Endpoint pre-approval state]` + `[Why we are submitting...]` 兩段
- [ ] Privacy policy URL 已填（`https://azuma520.github.io/threads-pipeline/privacy.html` 或當前部署 URL）
- [ ] Data deletion URL 已填（同上 `/data-deletion.html`）
- [ ] App icon 已上傳（`assets/app-icon.png`）
- [ ] Submit
