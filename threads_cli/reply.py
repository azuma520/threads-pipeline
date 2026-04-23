"""threads reply 子命令群——add / hide / unhide。

- add: 建立新回覆（原 top-level `threads reply <post_id> <text>`，批次 B3 遷移）
- hide / unhide: 管理別人對你貼文的回覆（App Review manage_replies 需求）
"""

import sys

import requests
import typer

from threads_pipeline.publisher import reply_to, PublishError
from threads_pipeline.threads_client import hide_reply
from threads_pipeline.threads_cli.output import (
    emit_envelope_json,
    error,
    error_with_code,
)
from threads_pipeline.threads_cli.safety import (
    require_token,
    validate_confirm_yes,
    interactive_confirm,
)

reply_app = typer.Typer(help="Reply operations (add / hide / unhide)", no_args_is_help=True)


@reply_app.command("add")
def add_cmd(
    post_id: str = typer.Argument(..., help="Parent post ID"),
    text: str = typer.Argument(..., help="Reply text"),
    confirm: bool = typer.Option(False, "--confirm", help="Actually reply (default: dry-run)"),
    yes: bool = typer.Option(False, "--yes", help="Skip interactive confirmation (Agent mode)"),
):
    """Reply to an existing post."""
    token = require_token()
    is_tty = sys.stdin.isatty()
    validate_confirm_yes(confirm=confirm, yes=yes, is_tty=is_tty)

    char_count = len(text)

    if not confirm:
        print(f"[DRY RUN] Would reply to post {post_id}:")
        print("---------------------------------")
        print(text)
        print("---------------------------------")
        print(f"Character count: {char_count}")
        print("Add --confirm to actually reply.")
        return

    if not yes:
        print(f"About to reply to post {post_id}:")
        print("---------------------------------")
        print(text)
        print("---------------------------------")
        if not interactive_confirm():
            print("(cancelled)")
            return

    try:
        reply_id = reply_to(post_id, text, token=token)
    except PublishError as e:
        error(str(e), exit_code=1)

    print(f"[OK] Reply posted as {reply_id} (parent: {post_id})")


def _perform_hide(reply_id: str, hide: bool, json_mode: bool) -> None:
    """共用實作：hide / unhide 只差 hide 旗標。"""
    token = require_token(json_mode=json_mode)
    try:
        hide_reply(reply_id=reply_id, token=token, hide=hide)
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else 0
        code = "NOT_FOUND" if status == 404 else "API_ERROR"
        error_with_code(code, f"HTTP {status}: {e}", json_mode=json_mode, exit_code=1)
    except requests.exceptions.RequestException as e:
        error_with_code("API_ERROR", f"Threads API error: {e}", json_mode=json_mode, exit_code=1)

    if json_mode:
        emit_envelope_json({"hidden": hide, "reply_id": reply_id})
        return

    action = "Hidden" if hide else "Unhidden"
    print(f"[OK] {action} reply {reply_id}")


@reply_app.command("hide")
def hide_cmd(
    reply_id: str = typer.Argument(..., help="Reply ID to hide"),
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON envelope"),
):
    """Hide a reply on your post."""
    _perform_hide(reply_id, hide=True, json_mode=json_mode)


@reply_app.command("unhide")
def unhide_cmd(
    reply_id: str = typer.Argument(..., help="Reply ID to unhide"),
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON envelope"),
):
    """Unhide a previously-hidden reply."""
    _perform_hide(reply_id, hide=False, json_mode=json_mode)
