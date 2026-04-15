"""Threads CLI 入口 — argparse + dispatch table。"""

import argparse
import sys

# Windows UTF-8：reconfigure 在 Python 啟動後才有效，setdefault("PYTHONUTF8", "1") 無用
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from threads_pipeline.threads_cli import __version__
from threads_pipeline.threads_cli.output import emit, error, warn


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
    """threads post publish — Task 6 實作。"""
    error("post publish: not implemented yet (pending task)", exit_code=2)


@_register("post.publish-chain")
def cmd_post_publish_chain(args) -> int:
    """threads post publish-chain — Task 8 實作。"""
    error("post publish-chain: not implemented yet (pending task)", exit_code=2)


@_register("reply")
def cmd_reply(args) -> int:
    """threads reply — Task 7 實作。"""
    error("reply: not implemented yet (pending task)", exit_code=2)


def main(argv: list[str] | None = None) -> int:
    """CLI 入口。"""
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
