"""Threads CLI 入口 — argparse + dispatch table。"""

import argparse
import sys

# Windows UTF-8：reconfigure 在 Python 啟動後才有效，setdefault("PYTHONUTF8", "1") 無用
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from threads_pipeline.threads_cli import __version__
from threads_pipeline.threads_cli.output import emit, error, warn
from threads_pipeline.publisher import (
    publish_text,
    reply_to,
    publish_chain,
    PublishError,
    ChainMidwayError,
)
from threads_pipeline.threads_cli.safety import (
    require_token,
    validate_confirm_yes,
    interactive_confirm,
)


def _build_parser() -> argparse.ArgumentParser:
    """建立 argparse parser 樹。"""
    parser = argparse.ArgumentParser(
        prog="threads",
        description="Threads API operations CLI (CLI-Anything compatible)",
    )
    parser.add_argument(
        "--version", action="version", version=f"threads {__version__}"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output as JSON (batch A: parsed but inert)"
    )

    subparsers = parser.add_subparsers(dest="resource", required=False)

    # posts (複數：列表操作) — 批次 B
    posts = subparsers.add_parser("posts", help="Posts list operations (batch B)")
    posts_sub = posts.add_subparsers(dest="action", required=True)

    posts_search = posts_sub.add_parser("search", help="Search posts by keyword")
    posts_search.add_argument("keyword", help="Search keyword")
    posts_search.add_argument("--limit", type=int, default=25, help="Max results (capped at 25)")

    # post (單數：單項操作)
    post = subparsers.add_parser("post", help="Single post operations")
    post_sub = post.add_subparsers(dest="action", required=True)

    post_publish = post_sub.add_parser("publish", help="Publish a post")
    post_publish.add_argument("text", help="Post text content")
    post_publish.add_argument("--confirm", action="store_true", help="Actually publish (default: dry-run)")
    post_publish.add_argument("--yes", action="store_true", help="Skip interactive confirmation (Agent mode)")

    post_chain = post_sub.add_parser("publish-chain", help="Publish a thread chain")
    post_chain.add_argument("file", help="Input file (- for stdin)")
    post_chain.add_argument("--confirm", action="store_true")
    post_chain.add_argument("--yes", action="store_true")
    post_chain.add_argument(
        "--on-failure",
        choices=["stop", "retry", "rollback"],
        default="stop",
        help="Mid-chain failure policy (Level 1 only implements 'stop')",
    )

    # reply
    reply = subparsers.add_parser("reply", help="Reply to an existing post")
    reply.add_argument("post_id", help="Parent post ID")
    reply.add_argument("text", help="Reply text")
    reply.add_argument("--confirm", action="store_true")
    reply.add_argument("--yes", action="store_true")

    return parser


# Dispatch table: resource.action → handler
COMMANDS: dict[str, callable] = {}


def _register(key: str):
    """Decorator 註冊子命令 handler。"""
    def _wrap(fn):
        COMMANDS[key] = fn
        return fn
    return _wrap


@_register("posts.search")
def cmd_posts_search(args) -> int:
    """threads posts search — 批次 B 實作。"""
    error("posts search: not implemented in batch A (pending batch B)", exit_code=2)


@_register("post.publish")
def cmd_post_publish(args) -> int:
    """threads post publish — 發單則貼文。"""
    token = require_token()
    is_tty = sys.stdin.isatty()
    validate_confirm_yes(confirm=args.confirm, yes=args.yes, is_tty=is_tty)

    text = args.text
    char_count = len(text)

    # Dry-run 預設
    if not args.confirm:
        print("[DRY RUN] Would publish:")
        print("---------------------------------")
        print(text)
        print("---------------------------------")
        print(f"Character count: {char_count}")
        print("Add --confirm to actually publish.")
        return 0

    # 互動確認（TTY + --confirm 無 --yes）
    if not args.yes:
        print("About to publish:")
        print("---------------------------------")
        print(text)
        print("---------------------------------")
        print(f"Character count: {char_count}")
        if not interactive_confirm():
            print("(cancelled)")
            return 0

    # 真正發文
    try:
        post_id = publish_text(text, token=token)
    except PublishError as e:
        error(str(e), exit_code=1)  # raises SystemExit, no unreachable return after

    print(f"[OK] Published as post {post_id}")
    return 0


@_register("post.publish-chain")
def cmd_post_publish_chain(args) -> int:
    """threads post publish-chain FILE — 串文發文。"""
    token = require_token()
    is_tty = sys.stdin.isatty()
    validate_confirm_yes(confirm=args.confirm, yes=args.yes, is_tty=is_tty)

    # 讀取輸入
    if args.file == "-":
        content = sys.stdin.read()
    else:
        try:
            with open(args.file, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            error(f"Cannot read file {args.file}: {e}", exit_code=1)

    # 空行分隔規則：一則 post = 一行，空行忽略
    # 注意：不支援多段落同一則（Level 1 限制）
    texts = [line.strip() for line in content.splitlines() if line.strip()]
    if not texts:
        error("No non-empty lines in input", exit_code=1)

    total_chars = sum(len(t) for t in texts)

    # Dry-run
    if not args.confirm:
        print(f"[DRY RUN] Would publish chain of {len(texts)} posts:")
        print("---------------------------------")
        for i, t in enumerate(texts):
            label = "opener" if i == 0 else "reply"
            print(f"{i + 1}/{len(texts)} ({label}):\t{t} ({len(t)} chars)")
        print("---------------------------------")
        print(f"Total: {len(texts)} posts, {total_chars} chars")
        print(f"On-failure policy: {args.on_failure}")
        print("Add --confirm to actually publish.")
        return 0

    # 互動確認
    if not args.yes:
        print(f"About to publish chain of {len(texts)} posts:")
        for i, t in enumerate(texts):
            preview = t[:60] + ("..." if len(t) > 60 else "")
            print(f"  {i + 1}. {preview}")
        if not interactive_confirm():
            print("(cancelled)")
            return 0

    # 真正發
    # IMPORTANT: ChainMidwayError IS-A PublishError — 保持 subclass 在前
    try:
        post_ids = publish_chain(texts, token=token, on_failure=args.on_failure)
    except NotImplementedError as e:
        error(str(e), exit_code=2)
    except ChainMidwayError as e:
        print(f"[ERROR] Chain failed at post {e.failed_index + 1}", file=sys.stderr)
        print(f"  Already posted IDs: {e.posted_ids}", file=sys.stderr)
        print(f"  Cause: {e.cause}", file=sys.stderr)
        print(f"  Recovery: manually delete or continue from post {e.failed_index + 1}", file=sys.stderr)
        return 1
    except PublishError as e:
        error(str(e), exit_code=1)

    print(f"[OK] Published chain of {len(post_ids)} posts:")
    for i, pid in enumerate(post_ids):
        print(f"  {i + 1}. {pid}")
    return 0


@_register("reply")
def cmd_reply(args) -> int:
    """threads reply <post_id> <text> — 回覆既有貼文。"""
    token = require_token()
    is_tty = sys.stdin.isatty()
    validate_confirm_yes(confirm=args.confirm, yes=args.yes, is_tty=is_tty)

    parent_id = args.post_id
    text = args.text
    char_count = len(text)

    if not args.confirm:
        print(f"[DRY RUN] Would reply to post {parent_id}:")
        print("---------------------------------")
        print(text)
        print("---------------------------------")
        print(f"Character count: {char_count}")
        print("Add --confirm to actually reply.")
        return 0

    if not args.yes:
        print(f"About to reply to post {parent_id}:")
        print("---------------------------------")
        print(text)
        print("---------------------------------")
        if not interactive_confirm():
            print("(cancelled)")
            return 0

    try:
        reply_id = reply_to(parent_id, text, token=token)
    except PublishError as e:
        error(str(e), exit_code=1)  # SystemExit

    print(f"[OK] Reply posted as {reply_id} (parent: {parent_id})")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI 入口。"""
    # 載入 .env（與 advisor / main 的 _load_dotenv 一致）
    try:
        from threads_pipeline.main import _load_dotenv
        _load_dotenv()
    except Exception:
        pass  # .env 載入失敗不擋 CLI（可能用外部 env）

    parser = _build_parser()
    args = parser.parse_args(argv)

    # 沒指定 resource → 印 help
    if args.resource is None:
        parser.print_help()
        return 0

    # 組 dispatch key（defensive：reply 沒有 action 屬性）
    if args.resource == "reply":
        key = "reply"
    else:
        action = getattr(args, "action", None)
        if action is None:
            # 理論上 subparsers required=True 會先攔下，但加保險
            error(f"Missing action for resource '{args.resource}'", exit_code=2)
        key = f"{args.resource}.{action}"

    handler = COMMANDS.get(key)
    if handler is None:
        error(f"Unknown command: {key}", exit_code=2)
    return handler(args) or 0


if __name__ == "__main__":
    sys.exit(main())
