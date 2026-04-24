"""Fetch a Threads post + classified threads/replies via Playwright + Relay JSON.

Prototype usage:

    pip install -e ".[dev,prototype]"
    playwright install chromium
    python scripts/fetch_threads_post.py "https://www.threads.com/@user/post/CODE"

Output: drafts/library/{YYYY-MM-DD}_{author}_{code}/{post.md, meta.json, screenshot.png}
"""
from __future__ import annotations

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
