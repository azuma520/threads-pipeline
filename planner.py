"""advisor plan 串文骨架生成器。"""

from __future__ import annotations

import re
from datetime import datetime, timezone

_ILLEGAL_FILENAME = re.compile(r'[/\\:*?"<>|]')
_WHITESPACE = re.compile(r"\s+")
_MAX_SLUG_LEN = 20


def slugify(topic: str) -> str:
    """把題目轉成檔名安全的 slug。保留中文，英文轉小寫，長度 ≤20。"""
    if not topic:
        return _timestamp_slug()
    cleaned = _ILLEGAL_FILENAME.sub("", topic).strip()
    cleaned = _WHITESPACE.sub("-", cleaned)
    cleaned = cleaned.lower()
    cleaned = cleaned[:_MAX_SLUG_LEN]
    if not cleaned or all(c == "-" for c in cleaned):
        return _timestamp_slug()
    return cleaned


def _timestamp_slug() -> str:
    now = datetime.now(timezone.utc)
    return f"plan-{now.strftime('%Y%m%d-%H%M')}"
