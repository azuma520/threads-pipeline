"""threads posts 子命令群——list / search。

設計要點：
- 兩個指令都支援 --limit / --json；list 另支援 --cursor 分頁
- 分頁策略（spec §1 拍板）：只抓第一頁，有下一頁時 stderr 提示 / envelope 帶 next_cursor
- limit 超上限（100）自動 clamp + LIMIT_CLAMPED warning
"""

import sys

import requests
import typer

from threads_pipeline.threads_client import list_my_posts
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
    token = require_token()
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


# Task 8 會在此檔下方追加 search_cmd
