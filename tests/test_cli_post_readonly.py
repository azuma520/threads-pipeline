"""threads post insights / replies 指令的 CliRunner 測試。"""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from threads_pipeline.threads_cli.cli import app

runner = CliRunner()


# === post insights ===

def test_post_insights_human_mode():
    fake = {"data": [
        {"name": "views", "values": [{"value": 100}]},
        {"name": "likes", "values": [{"value": 5}]},
    ]}
    with patch("threads_pipeline.threads_cli.post.fetch_post_insights_cli",
               return_value=fake), \
         patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, ["post", "insights", "POST_123"])
    assert result.exit_code == 0
    assert "views" in result.output
    assert "100" in result.output


def test_post_insights_json_mode():
    fake = {"data": [{"name": "views", "values": [{"value": 42}]}]}
    with patch("threads_pipeline.threads_cli.post.fetch_post_insights_cli",
               return_value=fake), \
         patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, ["post", "insights", "POST_123", "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed == {"ok": True, "data": fake}


def test_post_insights_not_found_json_mode():
    """404 → NOT_FOUND error envelope + exit 1。"""
    import requests
    resp = requests.Response()
    resp.status_code = 404
    err = requests.exceptions.HTTPError(response=resp)
    with patch("threads_pipeline.threads_cli.post.fetch_post_insights_cli",
               side_effect=err), \
         patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, ["post", "insights", "NONEXISTENT", "--json"])
    assert result.exit_code == 1
    parsed = json.loads(result.output.strip().split("\n")[0])
    assert parsed["ok"] is False
    assert parsed["error"]["code"] == "NOT_FOUND"


# === post replies ===

def test_post_replies_human_mode():
    fake = {"replies": [
        {"id": "R1", "text": "nice", "username": "user1"},
        {"id": "R2", "text": "thanks", "username": "user2"},
    ], "next_cursor": None}
    with patch("threads_pipeline.threads_cli.post.fetch_post_replies",
               return_value=fake), \
         patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, ["post", "replies", "POST_1"])
    assert result.exit_code == 0
    assert "R1" in result.output
    assert "nice" in result.output
    assert "user1" in result.output


def test_post_replies_json_mode_with_cursor():
    fake = {"replies": [{"id": "R1"}], "next_cursor": "CUR"}
    with patch("threads_pipeline.threads_cli.post.fetch_post_replies",
               return_value=fake), \
         patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, ["post", "replies", "POST_1", "--json"])
    parsed = json.loads(result.output)
    assert parsed["ok"] is True
    assert parsed["data"]["replies"] == [{"id": "R1"}]
    assert parsed["next_cursor"] == "CUR"


def test_post_replies_passes_limit_and_cursor():
    """--limit / --cursor 以 keyword 傳到 core helper。"""
    with patch("threads_pipeline.threads_cli.post.fetch_post_replies",
               return_value={"replies": [], "next_cursor": None}) as mock_fn, \
         patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        runner.invoke(app, ["post", "replies", "POST_1", "--limit", "50", "--cursor", "PREV"])
    assert mock_fn.call_args.kwargs["limit"] == 50
    assert mock_fn.call_args.kwargs["cursor"] == "PREV"
