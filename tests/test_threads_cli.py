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


def test_cli_publish_chain_reads_file(tmp_path):
    """從檔案讀多行，dry-run 印出清單。"""
    from threads_pipeline.threads_cli.cli import main

    chain_file = tmp_path / "chain.txt"
    chain_file.write_text("第一則\n第二則\n第三則\n", encoding="utf-8")

    with patch("threads_pipeline.threads_cli.cli.publish_chain") as mock_chain, \
         patch("threads_pipeline.threads_cli.cli.require_token", return_value="fake"):
        rc = main(["post", "publish-chain", str(chain_file)])

    assert rc == 0
    assert mock_chain.call_count == 0  # dry-run 不呼叫


def test_cli_publish_chain_confirm_yes_calls_api(tmp_path):
    """--confirm --yes 應呼叫 publish_chain。"""
    from threads_pipeline.threads_cli.cli import main

    chain_file = tmp_path / "chain.txt"
    chain_file.write_text("a\nb\nc\n", encoding="utf-8")

    with patch("threads_pipeline.threads_cli.cli.publish_chain", return_value=["1", "2", "3"]) as mock_chain, \
         patch("threads_pipeline.threads_cli.cli.require_token", return_value="fake"):
        rc = main(["post", "publish-chain", str(chain_file), "--confirm", "--yes"])

    assert rc == 0
    mock_chain.assert_called_once()
    assert mock_chain.call_args.args[0] == ["a", "b", "c"]


def test_cli_publish_chain_on_failure_not_stop_exit_2(tmp_path):
    """--on-failure=retry 應因 NotImplementedError 而 exit 2。"""
    from threads_pipeline.threads_cli.cli import main

    chain_file = tmp_path / "chain.txt"
    chain_file.write_text("a\n", encoding="utf-8")

    with patch("threads_pipeline.threads_cli.cli.require_token", return_value="fake"):
        with pytest.raises(SystemExit) as exc_info:
            main(["post", "publish-chain", str(chain_file),
                  "--confirm", "--yes", "--on-failure", "retry"])
    assert exc_info.value.code == 2
