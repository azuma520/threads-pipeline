"""threads account 子命令群——info / insights。"""

import requests
import typer

from threads_pipeline.threads_client import (
    fetch_account_info,
    fetch_account_insights_cli,
    list_mentions,
)
from threads_pipeline.threads_cli.output import (
    emit_envelope_json,
    error_with_code,
    warn_with_code,
)
from threads_pipeline.threads_cli.safety import require_token

account_app = typer.Typer(help="Account operations", no_args_is_help=True)


@account_app.command("info")
def info_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON envelope"),
):
    """Fetch account basic info (/me)."""
    token = require_token(json_mode=json_mode)
    try:
        data = fetch_account_info(token)
    except requests.exceptions.RequestException as e:
        error_with_code("API_ERROR", f"Threads API error: {e}", json_mode=json_mode, exit_code=1)

    if json_mode:
        emit_envelope_json(data)
        return

    # 人類模式
    print("[OK] Account info:")
    print(f"  id:          {data.get('id', '(missing)')}")
    print(f"  username:    {data.get('username', '(missing)')}")
    if bio := data.get("threads_biography"):
        print(f"  biography:   {bio}")
    if pic := data.get("threads_profile_picture_url"):
        print(f"  profile_pic: {pic}")


@account_app.command("insights")
def insights_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON envelope"),
):
    """Fetch account-level insights (views / followers 等)."""
    token = require_token(json_mode=json_mode)
    try:
        data = fetch_account_insights_cli(token)
    except requests.exceptions.RequestException as e:
        error_with_code("API_ERROR", f"Threads API error: {e}", json_mode=json_mode, exit_code=1)

    if json_mode:
        emit_envelope_json(data)
        return

    print("[OK] Account insights:")
    for metric in data.get("data", []):
        name = metric.get("name", "?")
        values = metric.get("values", [])
        total = metric.get("total_value", {})
        if values:
            val = values[0].get("value")
        elif total:
            val = total.get("value")
        else:
            val = "(no data)"
        print(f"  {name:30s} {val}")


_LIMIT_MAX_MENTIONS = 100


@account_app.command("mentions")
def mentions_cmd(
    limit: int = typer.Option(25, "--limit", help=f"Max mentions (1-{_LIMIT_MAX_MENTIONS})"),
    cursor: str | None = typer.Option(None, "--cursor", help="Pagination cursor"),
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON envelope"),
):
    """List @mentions of your account (paged; use --cursor for next page)."""
    token = require_token(json_mode=json_mode)

    warnings: list[dict[str, str]] = []
    effective_limit = limit
    if effective_limit > _LIMIT_MAX_MENTIONS:
        warnings.append(warn_with_code(
            "LIMIT_CLAMPED",
            f"limit 從 {limit} clamp 到 {_LIMIT_MAX_MENTIONS}",
        ))
        effective_limit = _LIMIT_MAX_MENTIONS
    if effective_limit < 1:
        warnings.append(warn_with_code("LIMIT_CLAMPED", "limit clamp 到 1"))
        effective_limit = 1

    try:
        result = list_mentions(token=token, limit=effective_limit, cursor=cursor)
    except requests.exceptions.RequestException as e:
        error_with_code("API_ERROR", f"Threads API error: {e}", json_mode=json_mode, exit_code=1)

    mentions = result["mentions"]
    next_cursor = result["next_cursor"]

    if json_mode:
        emit_envelope_json({"mentions": mentions}, warnings=warnings, next_cursor=next_cursor)
        return

    if not mentions:
        print("[OK] 尚無 mentions。")
        return

    print(f"[OK] {len(mentions)} mention(s):")
    for m in mentions:
        mid = m.get("id", "?")
        user = m.get("username", "?")
        text = (m.get("text") or "").replace("\n", " ")
        preview = text[:80] + ("..." if len(text) > 80 else "")
        print(f"  {mid}  @{user}  {preview}")

    if next_cursor:
        import sys
        print(
            f"[INFO] 還有更多資料。下一頁請加：--cursor {next_cursor}",
            file=sys.stderr,
        )
