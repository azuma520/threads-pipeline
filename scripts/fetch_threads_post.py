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
