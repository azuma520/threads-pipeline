"""threads posts 子命令群——list / search。

設計要點：
- 兩個指令都支援 --limit / --json；list 另支援 --cursor 分頁
- 分頁策略（spec §1 拍板）：只抓第一頁，有下一頁時 stderr 提示 / envelope 帶 next_cursor
- limit 超上限（100）自動 clamp + LIMIT_CLAMPED warning
"""

import sys

import requests
import typer

from threads_pipeline.threads_client import list_my_posts, _search_keyword
from threads_pipeline.threads_cli.output import (
    emit_envelope_json,
    error_with_code,
    warn_with_code,
)
from threads_pipeline.threads_cli.safety import require_token

_LIMIT_MAX = 100

posts_app = typer.Typer(help="Posts list / search operations", no_args_is_help=True)


def _clamp_limit(limit: int) -> tuple[int, list[dict[str, str]]]:
    """Clamp limit 到 [1, 100]；回傳 (effective_limit, warnings).

    副作用：`warn_with_code` 會寫 stderr（`[WARN]` 前綴）。
    JSON mode 下 stderr 仍會出現此訊息——為 spec §3 規定
    （warnings 同時走 envelope 與 stderr，人類與 Agent 都看得到）。
    """
    warnings: list[dict[str, str]] = []
    if limit > _LIMIT_MAX:
        warnings.append(warn_with_code(
            "LIMIT_CLAMPED",
            f"limit 從 {limit} clamp 到 {_LIMIT_MAX}（API 上限）",
        ))
        limit = _LIMIT_MAX
    if limit < 1:
        warnings.append(warn_with_code(
            "LIMIT_CLAMPED",
            f"limit 從 {limit} clamp 到 1（最小值）",
        ))
        limit = 1
    return limit, warnings


@posts_app.command("list")
def list_cmd(
    limit: int = typer.Option(25, "--limit", help=f"Max posts to fetch (1-{_LIMIT_MAX})"),
    cursor: str | None = typer.Option(None, "--cursor", help="Pagination cursor from previous call"),
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON envelope"),
):
    """List your own posts (paged; use --cursor to fetch next page)."""
    token = require_token(json_mode=json_mode)
    effective_limit, warnings = _clamp_limit(limit)

    try:
        result = list_my_posts(token, limit=effective_limit, cursor=cursor)
    except requests.exceptions.RequestException as e:
        error_with_code("API_ERROR", f"Threads API error: {e}", json_mode=json_mode, exit_code=1)

    posts = result["posts"]
    next_cursor = result["next_cursor"]

    if json_mode:
        emit_envelope_json(posts_envelope_data(posts), warnings=warnings, next_cursor=next_cursor)
        return

    # 人類模式
    if not posts:
        print("[OK] 目前沒有貼文。")
        return

    print(f"[OK] {len(posts)} post(s):")
    for p in posts:
        pid = p.get("id", "?")
        ts = p.get("timestamp", "")
        text = (p.get("text") or "").replace("\n", " ")
        preview = text[:80] + ("..." if len(text) > 80 else "")
        print(f"  {pid}  {ts}  {preview}")

    if next_cursor:
        print(
            f"[INFO] 還有更多資料。下一頁請加：--cursor {next_cursor}",
            file=sys.stderr,
        )


def posts_envelope_data(posts: list[dict]) -> dict:
    """JSON envelope 的 data 區塊格式——包一層 {"posts": [...]} 保留未來擴充空間。"""
    return {"posts": posts}


def _contains_cjk(text: str) -> bool:
    """判斷字串是否含 CJK 字元（U+4E00..U+9FFF 為主）。"""
    for ch in text:
        cp = ord(ch)
        if 0x4E00 <= cp <= 0x9FFF:
            return True
        if 0x3400 <= cp <= 0x4DBF:
            return True
    return False


_SEARCH_HELP = (
    "Search posts by keyword.\n\n"
    "⚠️  Standard Access 限制：此指令只會搜尋「你自己」的貼文。\n"
    "    中文關鍵字通常回 0 筆（API 行為）。\n"
    "    Advanced Access 核准後才支援跨帳號 / 中文有效搜尋。\n"
    "    建議：列自己的貼文請改用 `threads posts list`。"
)


@posts_app.command("search", help=_SEARCH_HELP)
def search_cmd(
    keyword: str = typer.Argument(..., help="Search keyword"),
    limit: int = typer.Option(25, "--limit", help=f"Max results (1-{_LIMIT_MAX})"),
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON envelope"),
):
    """Search posts by keyword (Standard Access 下限制嚴重——見 --help)."""
    token = require_token(json_mode=json_mode)
    effective_limit, warnings = _clamp_limit(limit)

    has_cjk = _contains_cjk(keyword)

    try:
        posts = _search_keyword(
            keyword=keyword,
            token=token,
            sort_order="TOP",
            max_results=effective_limit,
        )
    except requests.exceptions.RequestException as e:
        error_with_code("API_ERROR", f"Threads API error: {e}", json_mode=json_mode, exit_code=1)

    if has_cjk and not posts:
        warnings.append(warn_with_code(
            "EMPTY_RESULT_CJK",
            "Standard Access 下中文關鍵字通常回 0 筆。建議改用 `threads posts list`。",
        ))
    elif not posts:
        warnings.append(warn_with_code(
            "EMPTY_RESULT",
            "若本應有結果，可能是 Standard Access 限制（只搜得到自己的貼文）。",
        ))

    if json_mode:
        emit_envelope_json({"posts": posts, "keyword": keyword}, warnings=warnings)
        return

    if not posts:
        print(f"[OK] 沒有找到 keyword=\"{keyword}\" 的貼文。")
        return

    print(f"[OK] {len(posts)} match(es) for keyword=\"{keyword}\":")
    for p in posts:
        pid = p.get("id", "?")
        ts = p.get("timestamp", "")
        text = (p.get("text") or "").replace("\n", " ")
        preview = text[:80] + ("..." if len(text) > 80 else "")
        print(f"  {pid}  {ts}  {preview}")
