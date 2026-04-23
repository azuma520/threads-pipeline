"""Threads CLI 入口——Typer app + subcommand groups。"""

import sys

# Windows UTF-8：reconfigure 在 Python 啟動後才有效
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import click
import typer

from threads_pipeline.threads_cli import __version__
from threads_pipeline.threads_cli.post import post_app
from threads_pipeline.threads_cli.posts import posts_app
from threads_pipeline.threads_cli.account import account_app
from threads_pipeline.threads_cli.reply import reply_app

app = typer.Typer(
    name="threads",
    help="Threads API operations CLI (CLI-Anything compatible)",
    no_args_is_help=True,
    add_completion=False,
)

app.add_typer(post_app, name="post")
app.add_typer(posts_app, name="posts")
app.add_typer(account_app, name="account")
app.add_typer(reply_app, name="reply")


def _version_callback(value: bool):
    if value:
        typer.echo(f"threads {__version__}")
        raise typer.Exit()


@app.callback()
def _root(
    version: bool = typer.Option(
        False, "--version", callback=_version_callback, is_eager=True,
        help="Show version and exit"
    ),
    json_mode: bool = typer.Option(
        False, "--json", help="Output as JSON (B1: parsed; B2: 唯讀指令啟用完整 envelope)"
    ),
):
    """Root callback for global flags."""
    pass


def main(argv: list[str] | None = None) -> int:
    """CLI entry point（保持批次 A 簽章：吃 argv、回 exit code）。"""
    # 載入 .env（批次 A lessons 1.3）
    try:
        from threads_pipeline.main import _load_dotenv
        _load_dotenv()
    except Exception:
        pass

    try:
        app(args=argv, standalone_mode=False)
        return 0
    except click.exceptions.UsageError as e:
        # Typer/Click 內建的 parser / usage error（例：缺 argument、未知 flag）
        e.show()
        if "--json" in (argv or sys.argv[1:]):
            from threads_pipeline.threads_cli.output import emit_error_json
            emit_error_json("INVALID_ARGS", str(e.format_message()))
        return 2
    except click.exceptions.Exit as e:
        # typer.Exit 繼承自 click.exceptions.Exit，統一接這層
        return e.exit_code
    except SystemExit as e:
        # handler 中 output.error() 用 sys.exit()，會走這裡
        if e.code is None:
            return 0
        try:
            return int(e.code)
        except (TypeError, ValueError):
            # e.code 若為 str（極少見於我方 code，但防禦性處理）
            return 1


if __name__ == "__main__":
    sys.exit(main())
