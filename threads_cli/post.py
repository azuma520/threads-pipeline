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


@post_app.command("publish-chain")
def publish_chain_cmd(
    file: str = typer.Argument(..., help="Input file (- for stdin)"),
    confirm: bool = typer.Option(False, "--confirm"),
    yes: bool = typer.Option(False, "--yes"),
    on_failure: str = typer.Option(
        "stop", "--on-failure",
        help="Mid-chain failure policy (Level 1 only implements 'stop')",
    ),
):
    """Publish a thread chain."""
    token = require_token()
    is_tty = sys.stdin.isatty()
    validate_confirm_yes(confirm=confirm, yes=yes, is_tty=is_tty)

    # 讀取輸入
    if file == "-":
        content = sys.stdin.read()
    else:
        try:
            with open(file, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            error(f"Cannot read file {file}: {e}", exit_code=1)

    # 空行分隔規則
    texts = [line.strip() for line in content.splitlines() if line.strip()]
    if not texts:
        error("No non-empty lines in input", exit_code=1)

    total_chars = sum(len(t) for t in texts)

    # Dry-run
    if not confirm:
        print(f"[DRY RUN] Would publish chain of {len(texts)} posts:")
        print("---------------------------------")
        for i, t in enumerate(texts):
            label = "opener" if i == 0 else "reply"
            print(f"{i + 1}/{len(texts)} ({label}):\t{t} ({len(t)} chars)")
        print("---------------------------------")
        print(f"Total: {len(texts)} posts, {total_chars} chars")
        print(f"On-failure policy: {on_failure}")
        print("Add --confirm to actually publish.")
        return

    # 互動確認
    if not yes:
        print(f"About to publish chain of {len(texts)} posts:")
        for i, t in enumerate(texts):
            preview = t[:60] + ("..." if len(t) > 60 else "")
            print(f"  {i + 1}. {preview}")
        if not interactive_confirm():
            print("(cancelled)")
            return

    # 驗參：on_failure 必須 choices 之一（Typer 不像 argparse 有 choices 語法，手動驗）
    if on_failure not in ("stop", "retry", "rollback"):
        error(f"Invalid --on-failure value: {on_failure}", exit_code=2)

    # 真正發
    # IMPORTANT: ChainMidwayError IS-A PublishError — subclass 在前
    try:
        post_ids = publish_chain(texts, token=token, on_failure=on_failure)
    except NotImplementedError as e:
        error(str(e), exit_code=2)
    except ChainMidwayError as e:
        print(f"[ERROR] Chain failed at post {e.failed_index + 1}", file=sys.stderr)
        print(f"  Already posted IDs: {e.posted_ids}", file=sys.stderr)
        print(f"  Cause: {e.cause}", file=sys.stderr)
        print(f"  Recovery: manually delete or continue from post {e.failed_index + 1}", file=sys.stderr)
        raise typer.Exit(code=1)
    except PublishError as e:
        error(str(e), exit_code=1)

    print(f"[OK] Published chain of {len(post_ids)} posts:")
    for i, pid in enumerate(post_ids):
        print(f"  {i + 1}. {pid}")
