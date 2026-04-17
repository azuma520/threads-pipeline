"""CLI 安全層：Token 檢查、--confirm/--yes 驗證、互動確認。"""

import os
import sys

from threads_pipeline.threads_cli.output import error_with_code


def require_token(*, json_mode: bool = False) -> str:
    """取得 THREADS_ACCESS_TOKEN；缺失則 exit 1（json_mode 時吐 envelope）。"""
    token = os.environ.get("THREADS_ACCESS_TOKEN", "")
    if not token:
        error_with_code(
            "TOKEN_MISSING",
            "THREADS_ACCESS_TOKEN not set. "
            "Add it to .env or export as environment variable.",
            json_mode=json_mode,
            exit_code=1,
        )
    return token


def validate_confirm_yes(*, confirm: bool, yes: bool, is_tty: bool) -> None:
    """驗證 --confirm / --yes 組合合法性。

    規則：
    - --yes 無 --confirm → hard-error exit 2
    - 非 TTY + --confirm 無 --yes → hard-error exit 2
    - 其他合法組合（含無 flag）→ 返回，不拋例外
    """
    if yes and not confirm:
        print(
            "[ERROR] --yes requires --confirm. "
            "Without --confirm the command runs as dry-run.",
            file=sys.stderr,
        )
        sys.exit(2)

    if confirm and not yes and not is_tty:
        print(
            "[ERROR] --confirm requires --yes in non-interactive environments "
            "(CI / piped input / no TTY).",
            file=sys.stderr,
        )
        sys.exit(2)


def interactive_confirm(prompt: str = "Proceed?") -> bool:
    """TTY 互動確認；預設 N，EOFError / KeyboardInterrupt 視為取消。"""
    try:
        answer = input(f"{prompt} [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n(cancelled)", file=sys.stderr)
        return False
    return answer == "y"
