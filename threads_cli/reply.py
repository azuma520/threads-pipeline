"""threads reply 指令（top-level）。"""

import sys

import typer

from threads_pipeline.publisher import reply_to, PublishError
from threads_pipeline.threads_cli.output import error
from threads_pipeline.threads_cli.safety import (
    require_token,
    validate_confirm_yes,
    interactive_confirm,
)


def reply_cmd(
    post_id: str = typer.Argument(..., help="Parent post ID"),
    text: str = typer.Argument(..., help="Reply text"),
    confirm: bool = typer.Option(False, "--confirm"),
    yes: bool = typer.Option(False, "--yes"),
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
