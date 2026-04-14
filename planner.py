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


_FRAMEWORK_ROW = re.compile(
    r"^\|\s*(\d{2})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$",
    re.MULTILINE,
)


def _slice_structure_overview(md: str) -> str:
    """只取『## 結構總覽』到下一個 '## ' 之間的文字，避免誤吃『4 類結尾』等其他表格。"""
    m = re.search(r"^##\s*結構總覽\s*$", md, re.MULTILINE)
    if not m:
        return md  # fallback：整份都吃（regex 對中文第一欄的結尾表天然不匹配，但加 anchor 更穩）
    start = m.end()
    next_section = re.search(r"^##\s+", md[start:], re.MULTILINE)
    end = start + next_section.start() if next_section else len(md)
    return md[start:end]


def list_frameworks(md: str) -> list[dict]:
    """從 frameworks markdown 解析出所有框架。只吃「結構總覽」表，忽略結尾類型表。"""
    section = _slice_structure_overview(md)
    out = []
    for m in _FRAMEWORK_ROW.finditer(section):
        fw_id = int(m.group(1))
        out.append({
            "id": fw_id,
            "name": m.group(2).strip(),
            "formula": m.group(3).strip(),
            "when_to_use": m.group(4).strip(),
        })
    return out


def extract_framework_section(md: str, key: int | str) -> str | None:
    """依編號或名稱取出單一框架的描述。回傳 '編號 名稱 | 公式 | 適用場景' 的多行字串。"""
    frameworks = list_frameworks(md)
    for fw in frameworks:
        if (isinstance(key, int) and fw["id"] == key) or (isinstance(key, str) and fw["name"] == key):
            return (
                f"編號：{fw['id']:02d}\n"
                f"名稱：{fw['name']}\n"
                f"公式：{fw['formula']}\n"
                f"適用場景：{fw['when_to_use']}"
            )
    return None
