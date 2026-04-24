"""threads profile 子命令群——lookup / posts。

實作 App Review 2026-04-23 本輪送審範圍的 `profile_discovery` CLI 面向。

設計要點：
- `lookup <url>`：旗艦指令，URL → 取公開貼文 text
- `posts <username>`：列某 user 的公開貼文（分頁）
- `get`（查 profile 基本資料）本輪**不實作**——user 真實 use case 是讀內文學習，
  profile 基本資料不是必要項

錯誤碼對應（與 demo-script-profile-discovery.md 附錄 A 一致）：
- `UNSUPPORTED_URL` — URL 格式不符
- `PERMISSION_REQUIRED` — HTTP 400 + "does not exist" 訊息
  （endpoint pre-approval locked，demo 影片 Step 6 會展示此錯誤）
- `POST_NOT_FOUND` — URL 解析成功但 shortcode 不在 recent posts 列表
- `API_ERROR` — 其他網路 / HTTP 錯誤
"""

import sys

import requests
import typer

from threads_pipeline.threads_client import (
    fetch_user_threads,
    resolve_post_by_url,
)
from threads_pipeline.threads_cli.output import (
    emit_envelope_json,
    error_with_code,
    warn_with_code,
)
from threads_pipeline.threads_cli.safety import require_token

profile_app = typer.Typer(
    help="Public profile discovery (URL → post text; list creator posts)",
    no_args_is_help=True,
)

_LIMIT_MAX = 100


def _clamp_limit(limit: int) -> tuple[int, list[dict[str, str]]]:
    """Clamp limit 到 [1, 100]；回傳 (effective_limit, warnings)。"""
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


def _map_http_error(e: requests.exceptions.HTTPError) -> tuple[str, str]:
    """將 HTTPError 對應到 (error_code, message)。

    profile_discovery endpoint 的 pre-approval 行為是 HTTP 400 + 錯誤訊息含
    "does not exist" / "missing permissions"——歸到 `PERMISSION_REQUIRED`。
    其他 HTTP 錯誤一律 `API_ERROR`。
    """
    status = e.response.status_code if e.response is not None else 0
    message = ""
    if e.response is not None:
        try:
            body = e.response.json()
            err = body.get("error") if isinstance(body, dict) else None
            if isinstance(err, dict):
                message = err.get("message", "")
        except ValueError:
            message = e.response.text[:200]
    full_msg = f"HTTP {status}: {message or str(e)}"
    if status == 400 and (
        "does not exist" in message.lower()
        or "missing permissions" in message.lower()
    ):
        return "PERMISSION_REQUIRED", full_msg
    return "API_ERROR", full_msg


@profile_app.command("lookup")
def lookup_cmd(
    url: str = typer.Argument(..., help="Threads post URL, e.g. https://www.threads.com/@user/post/XYZ"),
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON envelope"),
):
    """Look up a public Threads post by URL → fetch its full text for reading / study.

    Uses the profile_discovery endpoint (pre-approval this returns HTTP 400 —
    expected and shown as evidence in the App Review demo video).
    """
    token = require_token(json_mode=json_mode)

    post: dict = {}
    try:
        post = resolve_post_by_url(url=url, token=token)
    except ValueError as e:
        error_with_code("UNSUPPORTED_URL", str(e), json_mode=json_mode, exit_code=1)
    except LookupError as e:
        error_with_code("POST_NOT_FOUND", str(e), json_mode=json_mode, exit_code=1)
    except requests.exceptions.HTTPError as e:
        code, msg = _map_http_error(e)
        error_with_code(code, msg, json_mode=json_mode, exit_code=1)
    except requests.exceptions.RequestException as e:
        error_with_code("API_ERROR", f"Threads API error: {e}", json_mode=json_mode, exit_code=1)

    if json_mode:
        emit_envelope_json({"post": post})
        return

    pid = post.get("id", "?")
    username = post.get("username", "?")
    ts = post.get("timestamp", "")
    permalink = post.get("permalink", "")
    text = post.get("text") or ""

    print(f"[OK] Post {pid}")
    print(f"  username:  @{username}")
    print(f"  timestamp: {ts}")
    print(f"  permalink: {permalink}")
    print("  text:")
    for line in text.splitlines() or [""]:
        print(f"    {line}")


@profile_app.command("posts")
def posts_cmd(
    username: str = typer.Argument(..., help="Threads username (no leading @)"),
    limit: int = typer.Option(25, "--limit", help=f"Max posts to fetch (1-{_LIMIT_MAX})"),
    cursor: str | None = typer.Option(None, "--cursor", help="Pagination cursor from previous call"),
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON envelope"),
):
    """List a creator's recent public posts (for studying their style).

    Uses the profile_discovery endpoint (pre-approval this returns HTTP 400).
    """
    token = require_token(json_mode=json_mode)
    effective_limit, warnings = _clamp_limit(limit)

    # 使用者可能帶前導 @；剝掉
    clean_username = username.lstrip("@")

    result: dict = {"posts": [], "next_cursor": None}
    try:
        result = fetch_user_threads(
            username=clean_username,
            token=token,
            limit=effective_limit,
            cursor=cursor,
        )
    except requests.exceptions.HTTPError as e:
        code, msg = _map_http_error(e)
        error_with_code(code, msg, json_mode=json_mode, exit_code=1)
    except requests.exceptions.RequestException as e:
        error_with_code("API_ERROR", f"Threads API error: {e}", json_mode=json_mode, exit_code=1)

    posts = result["posts"]
    next_cursor = result["next_cursor"]

    if json_mode:
        emit_envelope_json(
            {"posts": posts, "username": clean_username},
            warnings=warnings,
            next_cursor=next_cursor,
        )
        return

    if not posts:
        print(f"[OK] @{clean_username} 尚無公開貼文。")
        return

    print(f"[OK] @{clean_username}: {len(posts)} post(s):")
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
