"""CLI 層單元測試——Typer CliRunner 模式。"""

from unittest.mock import patch

from typer.testing import CliRunner

from threads_pipeline.threads_cli.cli import app

runner = CliRunner()


# === publish ===

def test_cli_post_publish_dry_run():
    """無 --confirm 應 dry-run，不呼叫 publisher。"""
    with patch("threads_pipeline.threads_cli.post.publish_text") as mock_pub, \
         patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, ["post", "publish", "測試文字"])

    assert result.exit_code == 0
    assert mock_pub.call_count == 0
    assert "[DRY RUN]" in result.output


def test_cli_post_publish_confirm_yes_calls_api():
    """--confirm --yes 應呼叫 publish_text。"""
    with patch("threads_pipeline.threads_cli.post.publish_text", return_value="POST_ABC") as mock_pub, \
         patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, ["post", "publish", "hello", "--confirm", "--yes"])

    assert result.exit_code == 0
    mock_pub.assert_called_once()
    assert mock_pub.call_args.args[0] == "hello"


def test_cli_post_publish_yes_without_confirm_exit_2():
    """--yes 無 --confirm → exit 2。"""
    with patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, ["post", "publish", "x", "--yes"])
    assert result.exit_code == 2


# === reply ===

def test_cli_reply_dry_run():
    """reply 無 --confirm 應 dry-run。"""
    with patch("threads_pipeline.threads_cli.reply.reply_to") as mock_rep, \
         patch("threads_pipeline.threads_cli.reply.require_token", return_value="fake"):
        result = runner.invoke(app, ["reply", "add", "POST_123", "我的回覆"])

    assert result.exit_code == 0
    assert mock_rep.call_count == 0
    assert "[DRY RUN]" in result.output


def test_cli_reply_confirm_yes_calls_api():
    """reply --confirm --yes 應呼叫 reply_to。"""
    with patch("threads_pipeline.threads_cli.reply.reply_to", return_value="REPLY_ABC") as mock_rep, \
         patch("threads_pipeline.threads_cli.reply.require_token", return_value="fake"):
        result = runner.invoke(app, ["reply", "add", "POST_123", "回覆", "--confirm", "--yes"])

    assert result.exit_code == 0
    mock_rep.assert_called_once()
    assert mock_rep.call_args.args[0] == "POST_123"
    assert mock_rep.call_args.args[1] == "回覆"


# === publish-chain ===

def test_cli_publish_chain_reads_file(tmp_path):
    """從檔案讀多行，dry-run 印出清單。"""
    chain_file = tmp_path / "chain.txt"
    chain_file.write_text("第一則\n第二則\n第三則\n", encoding="utf-8")

    with patch("threads_pipeline.threads_cli.post.publish_chain") as mock_chain, \
         patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, ["post", "publish-chain", str(chain_file)])

    assert result.exit_code == 0
    assert mock_chain.call_count == 0
    assert "3 posts" in result.output


def test_cli_publish_chain_confirm_yes_calls_api(tmp_path):
    """--confirm --yes 應呼叫 publish_chain。"""
    chain_file = tmp_path / "chain.txt"
    chain_file.write_text("a\nb\nc\n", encoding="utf-8")

    with patch("threads_pipeline.threads_cli.post.publish_chain", return_value=["1", "2", "3"]) as mock_chain, \
         patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, ["post", "publish-chain", str(chain_file), "--confirm", "--yes"])

    assert result.exit_code == 0
    mock_chain.assert_called_once()
    assert mock_chain.call_args.args[0] == ["a", "b", "c"]


def test_cli_publish_chain_on_failure_not_stop_exit_2(tmp_path):
    """--on-failure=retry 應因 NotImplementedError 而 exit 2。"""
    chain_file = tmp_path / "chain.txt"
    chain_file.write_text("a\n", encoding="utf-8")

    with patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, [
            "post", "publish-chain", str(chain_file),
            "--confirm", "--yes", "--on-failure", "retry"
        ])
    assert result.exit_code == 2


# 註：subprocess-based version/help tests 的 canonical 位置在
# tests/test_cli_blackbox.py（test_bbox_version / test_bbox_help），
# 本檔只保留 Typer CliRunner 層的 in-process 測試。
