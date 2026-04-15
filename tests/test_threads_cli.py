"""CLI 層單元測試。"""

import subprocess
import sys
from unittest.mock import patch

import pytest


def test_threads_cli_version():
    """threads --version 應印出版本號。"""
    result = subprocess.run(
        [sys.executable, "-m", "threads_pipeline.threads_cli.cli", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "0.1.0" in result.stdout


def test_threads_cli_help():
    """threads --help 應印使用說明且 exit 0。"""
    result = subprocess.run(
        [sys.executable, "-m", "threads_pipeline.threads_cli.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "posts" in result.stdout or "post" in result.stdout


def test_cli_post_publish_dry_run():
    """無 --confirm 應 dry-run，不呼叫 publisher。"""
    from threads_pipeline.threads_cli.cli import main

    with patch("threads_pipeline.threads_cli.cli.publish_text") as mock_pub, \
         patch("threads_pipeline.threads_cli.cli.require_token", return_value="fake"):
        rc = main(["post", "publish", "測試文字"])

    assert rc == 0
    assert mock_pub.call_count == 0


def test_cli_post_publish_confirm_yes_calls_api():
    """--confirm --yes 應呼叫 publish_text。"""
    from threads_pipeline.threads_cli.cli import main

    with patch("threads_pipeline.threads_cli.cli.publish_text", return_value="POST_ABC") as mock_pub, \
         patch("threads_pipeline.threads_cli.cli.require_token", return_value="fake"):
        rc = main(["post", "publish", "hello", "--confirm", "--yes"])

    assert rc == 0
    mock_pub.assert_called_once()
    assert mock_pub.call_args.args[0] == "hello"


def test_cli_post_publish_yes_without_confirm_exit_2():
    """--yes 無 --confirm → exit 2。"""
    from threads_pipeline.threads_cli.cli import main

    with patch("threads_pipeline.threads_cli.cli.require_token", return_value="fake"):
        with pytest.raises(SystemExit) as exc_info:
            main(["post", "publish", "x", "--yes"])
    assert exc_info.value.code == 2


def test_cli_reply_dry_run():
    """reply 無 --confirm 應 dry-run。"""
    from threads_pipeline.threads_cli.cli import main

    with patch("threads_pipeline.threads_cli.cli.reply_to") as mock_rep, \
         patch("threads_pipeline.threads_cli.cli.require_token", return_value="fake"):
        rc = main(["reply", "POST_123", "我的回覆"])

    assert rc == 0
    assert mock_rep.call_count == 0


def test_cli_reply_confirm_yes_calls_api():
    """reply --confirm --yes 應呼叫 reply_to。"""
    from threads_pipeline.threads_cli.cli import main

    with patch("threads_pipeline.threads_cli.cli.reply_to", return_value="REPLY_ABC") as mock_rep, \
         patch("threads_pipeline.threads_cli.cli.require_token", return_value="fake"):
        rc = main(["reply", "POST_123", "回覆", "--confirm", "--yes"])

    assert rc == 0
    mock_rep.assert_called_once()
    assert mock_rep.call_args.args[0] == "POST_123"
    assert mock_rep.call_args.args[1] == "回覆"
