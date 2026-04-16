"""threads post 子命令群——publish / publish-chain。

注意：reply 是 top-level command（不在 post.py），見 threads_cli/reply.py。
"""

import sys

import typer

from threads_pipeline.publisher import (
    publish_text,
    publish_chain,
    PublishError,
    ChainMidwayError,
)
from threads_pipeline.threads_cli.output import error
from threads_pipeline.threads_cli.safety import (
    require_token,
    validate_confirm_yes,
    interactive_confirm,
)

post_app = typer.Typer(help="Single post operations", no_args_is_help=True)


@post_app.command("publish")
def publish_cmd(
    text: str = typer.Argument(..., help="Post text content"),
    confirm: bool = typer.Option(False, "--confirm", help="Actually publish (default: dry-run)"),
    yes: bool = typer.Option(False, "--yes", help="Skip interactive confirmation (Agent mode)"),
):
    """Publish a post."""
    token = require_token()
    is_tty = sys.stdin.isatty()
    validate_confirm_yes(confirm=confirm, yes=yes, is_tty=is_tty)

    char_count = len(text)

    # Dry-run 預設
    if not confirm:
        print("[DRY RUN] Would publish:")
        print("---------------------------------")
        print(text)
        print("---------------------------------")
        print(f"Character count: {char_count}")
        print("Add --confirm to actually publish.")
        return

    # 互動確認
    if not yes:
        print("About to publish:")
        print("---------------------------------")
        print(text)
        print("---------------------------------")
        print(f"Character count: {char_count}")
        if not interactive_confirm():
            print("(cancelled)")
            return

    # 真正發文
    try:
        post_id = publish_text(text, token=token)
    except PublishError as e:
        error(str(e), exit_code=1)

    print(f"[OK] Published as post {post_id}")


# Task 5 會在此檔下方 append publish_chain_cmd（sys / typer 等已 import，不需重複）
