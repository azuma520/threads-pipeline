"""threads post 子命令群——publish / reply / publish-chain / (B2: insights / replies / delete)。"""

import typer

post_app = typer.Typer(help="Single post operations", no_args_is_help=True)
# Task 4 會加入 publish handler、Task 5 加入 publish-chain handler
# （reply 是 top-level command，不在此檔——見 Task 6 的 reply.py）
