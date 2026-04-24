"""Fetch a Threads post + classified threads/replies via Playwright + Relay JSON.

Prototype usage:

    pip install -e ".[dev,prototype]"
    playwright install chromium
    python scripts/fetch_threads_post.py "https://www.threads.com/@user/post/CODE"

Output: drafts/library/{YYYY-MM-DD}_{author}_{code}/{post.md, meta.json, screenshot.png}
"""
from __future__ import annotations

import json
import pathlib
import re


_URL_RE = re.compile(
    r"threads\.(?:com|net)/@([\w.-]+)/post/([A-Za-z0-9_-]+)"
)


def parse_url(url: str) -> tuple[str, str]:
    """Return (username, code) extracted from a Threads post URL.

    Raises ValueError when the URL does not match the expected shape.
    """
    m = _URL_RE.search(url)
    if not m:
        raise ValueError(f"Not a Threads post URL: {url}")
    return m.group(1), m.group(2)


def classify(post: dict, main_author: str) -> str:
    """Classify a Relay post node into A/B/C/D/E.

    Schema: `is_reply` and `reply_to_author` are nested inside
    `post["text_post_app_info"]` in real Threads Relay payloads.

    A: main post (is_reply is False / missing)
    B: author-thread-extension — is_reply, author == main, reply_to == main
    C: author-replies-to-commenter — is_reply, author == main, reply_to != main
    D: other-user top-level reply — is_reply, author != main, reply_to == main
    E: deep reply / unknown — everything else
    """
    info = post.get("text_post_app_info") or {}
    if not info.get("is_reply"):
        return "A"
    author = (post.get("user") or {}).get("username") or ""
    reply_to_obj = info.get("reply_to_author") or {}
    reply_to = reply_to_obj.get("username") or ""
    if author == main_author and reply_to == main_author:
        return "B"
    if author == main_author and reply_to != main_author:
        return "C"
    if author != main_author and reply_to == main_author:
        return "D"
    return "E"


def walk_posts(data) -> list[dict]:
    """Recursively collect post-like dicts from a parsed Relay JSON blob.

    A node qualifies as a post only if it's a dict containing **all four** keys:
    `pk` (post primary key), `code`, `caption` (dict), `user` (dict). The `pk`
    requirement (I1) guards against preview/reference fragments that share the
    other three keys but do not carry the post PK — those would otherwise
    classify as false "A" main posts.

    Does not dedupe — callers handle that via `{p["code"]: p for p in ...}`
    because the same post can appear under multiple Relay query results.
    """
    found: list[dict] = []

    def _walk(node):
        if isinstance(node, dict):
            if (
                "pk" in node
                and "code" in node
                and isinstance(node.get("caption"), dict)
                and isinstance(node.get("user"), dict)
            ):
                found.append(node)
            for v in node.values():
                _walk(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(data)
    return found


_RELAY_QUERY_MARKER = "BarcelonaPostPageDirectQuery"
# I3: 匹配任何含 data-sjs 屬性的 <script>；屬性順序由 runtime 檢查以相容 Meta 變動。
_SCRIPT_RE = re.compile(
    r'<script([^>]*\bdata-sjs\b[^>]*)>(.*?)</script>',
    re.DOTALL,
)


def extract_relay_json(html: str) -> dict | None:
    """Return the parsed JSON of the `<script data-sjs>` whose content contains
    the Relay query marker and yields the **most post-shaped nodes** when walked.

    Implementation note: Threads 頁面通常有 7 支 script 都含 marker（query 定義、
    cache reference、metadata、實際結果），只有其中一支是實際查詢結果並內含
    post records。不可取「第一個含 marker」——必須對所有 candidate 跑
    `walk_posts` 計數，取最大。

    Accepts `data-sjs` attribute in any order relative to `type=` (I3). Requires
    both `data-sjs` **and** `type="application/json"`. Returns None if no marker
    script parses or all parsed scripts yield 0 post-shaped nodes.
    """
    best: dict | None = None
    best_count = 0
    for match in _SCRIPT_RE.finditer(html):
        attrs = match.group(1)
        if 'type="application/json"' not in attrs:
            continue
        payload = match.group(2)
        if _RELAY_QUERY_MARKER not in payload:
            continue
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            continue
        count = len(walk_posts(parsed))
        if count > best_count:
            best = parsed
            best_count = count
    return best


def filter_by_flags(
    posts_with_class: list[tuple[dict, str]],
    include_replies: bool,
    include_self_replies: bool,
) -> list[tuple[dict, str]]:
    """Filter classified posts. Default keeps A + B only. E is always dropped."""
    kept = {"A", "B"}
    if include_replies:
        kept.add("D")
    if include_self_replies:
        kept.add("C")
    return [(p, c) for p, c in posts_with_class if c in kept]


def render_markdown(
    posts_with_class: list[tuple[dict, str]],
    meta: dict,
) -> str:
    """Render a markdown document with YAML frontmatter + sections per class.

    Sections appear in A -> B -> C -> D order; E is ignored. Within a section,
    posts are sorted by `taken_at` ascending.
    """
    lines = ["---"]
    for key in ("author", "code", "url", "fetched_at"):
        lines.append(f"{key}: {meta[key]}")
    lines.append("---")
    lines.append("")

    by_class: dict[str, list[dict]] = {"A": [], "B": [], "C": [], "D": []}
    for p, c in posts_with_class:
        if c in by_class:
            by_class[c].append(p)

    for cls in ("A", "B", "C", "D"):
        for p in sorted(by_class[cls], key=lambda q: q.get("taken_at") or 0):
            username = (p.get("user") or {}).get("username", "")
            code = p.get("code", "")
            body = (p.get("caption") or {}).get("text", "") or ""
            lines.append(f"## [{cls}] @{username} · {code}")
            lines.append("")
            lines.append(body)
            lines.append("")

    return "\n".join(lines)


def write_output(
    out_root: pathlib.Path,
    meta: dict,
    markdown: str,
    relay_payload: dict,
    screenshot: bytes | None,
) -> pathlib.Path:
    """Write post.md / meta.json / relay.json / screenshot.png into
    `out_root/{date}_{author}_{code}/`.

    Returns the directory path. `fetched_at` must be an ISO 8601 timestamp
    whose first 10 chars form the date prefix.

    B1 note: meta.json contains the summary only (author/code/url/fetched_at/
    counts/kept/segments). The raw Relay payload is written to `relay.json` as
    a sibling, keeping meta.json human-readable and small.
    """
    date = meta["fetched_at"][:10]
    out_dir = out_root / f"{date}_{meta['author']}_{meta['code']}"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "post.md").write_text(markdown, encoding="utf-8")

    (out_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (out_dir / "relay.json").write_text(
        json.dumps(relay_payload, ensure_ascii=False),
        encoding="utf-8",
    )

    if screenshot:
        (out_dir / "screenshot.png").write_bytes(screenshot)

    return out_dir
