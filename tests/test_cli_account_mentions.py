"""CLI tests for threads account mentions."""

import json
from unittest.mock import patch

import requests
from typer.testing import CliRunner

from threads_pipeline.threads_cli.cli import app

runner = CliRunner()


def test_account_mentions_human_mode():
    fake = {
        "mentions": [
            {"id": "M1", "username": "alice", "text": "@you hey", "timestamp": "2026-04-23T00:00:00Z"},
            {"id": "M2", "username": "bob", "text": "@you look", "timestamp": "2026-04-23T00:01:00Z"},
        ],
        "next_cursor": None,
    }
    with patch("threads_pipeline.threads_cli.account.list_mentions", return_value=fake), \
         patch("threads_pipeline.threads_cli.account.require_token", return_value="fake"):
        result = runner.invoke(app, ["account", "mentions"])
    assert result.exit_code == 0
    assert "alice" in result.output
    assert "M1" in result.output
    assert "bob" in result.output


def test_account_mentions_empty():
    fake = {"mentions": [], "next_cursor": None}
    with patch("threads_pipeline.threads_cli.account.list_mentions", return_value=fake), \
         patch("threads_pipeline.threads_cli.account.require_token", return_value="fake"):
        result = runner.invoke(app, ["account", "mentions"])
    assert result.exit_code == 0
    assert "尚無" in result.output or "no mentions" in result.output.lower()


def test_account_mentions_json_mode():
    fake = {
        "mentions": [{"id": "M1", "username": "alice", "text": "@you"}],
        "next_cursor": "CUR_X",
    }
    with patch("threads_pipeline.threads_cli.account.list_mentions", return_value=fake), \
         patch("threads_pipeline.threads_cli.account.require_token", return_value="fake"):
        result = runner.invoke(app, ["account", "mentions", "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["ok"] is True
    assert parsed["data"] == {"mentions": [{"id": "M1", "username": "alice", "text": "@you"}]}
    assert parsed["next_cursor"] == "CUR_X"


def test_account_mentions_passes_limit_and_cursor():
    fake = {"mentions": [], "next_cursor": None}
    with patch("threads_pipeline.threads_cli.account.list_mentions", return_value=fake) as mock_lm, \
         patch("threads_pipeline.threads_cli.account.require_token", return_value="fake"):
        result = runner.invoke(app, ["account", "mentions", "--limit", "50", "--cursor", "PREV"])
    assert result.exit_code == 0
    mock_lm.assert_called_once_with(token="fake", limit=50, cursor="PREV")


def test_account_mentions_limit_clamped():
    """limit > 100 should clamp to 100 and emit LIMIT_CLAMPED warning."""
    fake = {"mentions": [], "next_cursor": None}
    with patch("threads_pipeline.threads_cli.account.list_mentions", return_value=fake) as mock_lm, \
         patch("threads_pipeline.threads_cli.account.require_token", return_value="fake"):
        result = runner.invoke(app, ["account", "mentions", "--limit", "500", "--json"])
    assert result.exit_code == 0
    mock_lm.assert_called_once_with(token="fake", limit=100, cursor=None)
    # CliRunner mix_stderr=True 會把 [WARN] stderr 合進 result.output，
    # 與 test_cli_posts_readonly.py 同樣用 `{`...`}` 配對切出 JSON envelope 再 parse
    json_start = result.output.find("{")
    json_end = result.output.rfind("}")
    assert json_start >= 0 and json_end > json_start, (
        f"no JSON envelope found in output: {result.output!r}"
    )
    parsed = json.loads(result.output[json_start:json_end + 1])
    assert any(w["code"] == "LIMIT_CLAMPED" for w in parsed.get("warnings", []))


def test_account_mentions_api_error_json_mode():
    err = requests.exceptions.RequestException("network down")
    with patch("threads_pipeline.threads_cli.account.list_mentions", side_effect=err), \
         patch("threads_pipeline.threads_cli.account.require_token", return_value="fake"):
        result = runner.invoke(app, ["account", "mentions", "--json"])
    assert result.exit_code == 1
    parsed = json.loads(result.output.strip().split("\n")[0])
    assert parsed["ok"] is False
    assert parsed["error"]["code"] == "API_ERROR"
