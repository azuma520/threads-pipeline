"""CLI 安全層測試。"""

from unittest.mock import patch

import pytest


def test_require_token_present():
    """Token 存在應回傳 token 值。"""
    from threads_pipeline.threads_cli.safety import require_token

    with patch.dict("os.environ", {"THREADS_ACCESS_TOKEN": "abc123"}):
        assert require_token() == "abc123"


def test_require_token_missing_exits_1():
    """Token 缺失應 exit 1。"""
    from threads_pipeline.threads_cli.safety import require_token

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(SystemExit) as exc_info:
            require_token()
    assert exc_info.value.code == 1


def test_validate_confirm_yes_yes_without_confirm_hard_error():
    """--yes 無 --confirm → exit 2。"""
    from threads_pipeline.threads_cli.safety import validate_confirm_yes

    with pytest.raises(SystemExit) as exc_info:
        validate_confirm_yes(confirm=False, yes=True, is_tty=True)
    assert exc_info.value.code == 2


def test_validate_confirm_yes_nontty_confirm_without_yes_hard_error():
    """非 TTY + --confirm 無 --yes → exit 2。"""
    from threads_pipeline.threads_cli.safety import validate_confirm_yes

    with pytest.raises(SystemExit) as exc_info:
        validate_confirm_yes(confirm=True, yes=False, is_tty=False)
    assert exc_info.value.code == 2


def test_validate_confirm_yes_tty_confirm_without_yes_ok():
    """TTY + --confirm 無 --yes 可執行（會進互動確認）。"""
    from threads_pipeline.threads_cli.safety import validate_confirm_yes

    validate_confirm_yes(confirm=True, yes=False, is_tty=True)  # no raise


def test_validate_confirm_yes_both_ok():
    """--confirm --yes 組合正確。"""
    from threads_pipeline.threads_cli.safety import validate_confirm_yes

    validate_confirm_yes(confirm=True, yes=True, is_tty=False)
    validate_confirm_yes(confirm=True, yes=True, is_tty=True)


def test_validate_confirm_yes_neither_ok():
    """沒 flag（純 dry-run）也合法。"""
    from threads_pipeline.threads_cli.safety import validate_confirm_yes

    validate_confirm_yes(confirm=False, yes=False, is_tty=True)
    validate_confirm_yes(confirm=False, yes=False, is_tty=False)


def test_interactive_confirm_yes_proceeds():
    """使用者輸入 y 應回傳 True。"""
    from threads_pipeline.threads_cli.safety import interactive_confirm

    with patch("builtins.input", return_value="y"):
        assert interactive_confirm() is True


def test_interactive_confirm_n_cancels():
    """使用者輸入 n 或 Enter 應回傳 False。"""
    from threads_pipeline.threads_cli.safety import interactive_confirm

    with patch("builtins.input", return_value=""):
        assert interactive_confirm() is False
    with patch("builtins.input", return_value="n"):
        assert interactive_confirm() is False


def test_interactive_confirm_eof_cancels():
    """EOFError 應視為取消（回 False）。"""
    from threads_pipeline.threads_cli.safety import interactive_confirm

    with patch("builtins.input", side_effect=EOFError):
        assert interactive_confirm() is False
