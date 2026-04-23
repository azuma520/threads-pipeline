"""CLI tests for threads reply hide / unhide."""

import json
from unittest.mock import patch

import requests
from typer.testing import CliRunner

from threads_pipeline.threads_cli.cli import app

runner = CliRunner()


# === reply hide ===

def test_reply_hide_human_mode():
    with patch("threads_pipeline.threads_cli.reply.hide_reply", return_value=True) as mock_hide, \
         patch("threads_pipeline.threads_cli.reply.require_token", return_value="fake"):
        result = runner.invoke(app, ["reply", "hide", "R_123"])
    assert result.exit_code == 0
    mock_hide.assert_called_once_with(reply_id="R_123", token="fake", hide=True)
    assert "Hidden" in result.output
    assert "R_123" in result.output


def test_reply_hide_json_mode():
    with patch("threads_pipeline.threads_cli.reply.hide_reply", return_value=True), \
         patch("threads_pipeline.threads_cli.reply.require_token", return_value="fake"):
        result = runner.invoke(app, ["reply", "hide", "R_123", "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed == {"ok": True, "data": {"hidden": True, "reply_id": "R_123"}}


def test_reply_hide_api_error_json_mode():
    err = requests.exceptions.RequestException("boom")
    with patch("threads_pipeline.threads_cli.reply.hide_reply", side_effect=err), \
         patch("threads_pipeline.threads_cli.reply.require_token", return_value="fake"):
        result = runner.invoke(app, ["reply", "hide", "R_123", "--json"])
    assert result.exit_code == 1
    parsed = json.loads(result.output.strip().split("\n")[0])
    assert parsed["ok"] is False
    assert parsed["error"]["code"] == "API_ERROR"


def test_reply_hide_404_maps_to_not_found():
    """404 should produce NOT_FOUND code, not generic API_ERROR."""
    fake_resp = requests.Response()
    fake_resp.status_code = 404
    err = requests.exceptions.HTTPError("404", response=fake_resp)
    with patch("threads_pipeline.threads_cli.reply.hide_reply", side_effect=err), \
         patch("threads_pipeline.threads_cli.reply.require_token", return_value="fake"):
        result = runner.invoke(app, ["reply", "hide", "BAD_ID", "--json"])
    assert result.exit_code == 1
    parsed = json.loads(result.output.strip().split("\n")[0])
    assert parsed["error"]["code"] == "NOT_FOUND"


# === reply unhide ===

def test_reply_unhide_human_mode():
    with patch("threads_pipeline.threads_cli.reply.hide_reply", return_value=True) as mock_hide, \
         patch("threads_pipeline.threads_cli.reply.require_token", return_value="fake"):
        result = runner.invoke(app, ["reply", "unhide", "R_456"])
    assert result.exit_code == 0
    mock_hide.assert_called_once_with(reply_id="R_456", token="fake", hide=False)
    assert "Unhidden" in result.output


def test_reply_unhide_json_mode():
    with patch("threads_pipeline.threads_cli.reply.hide_reply", return_value=True), \
         patch("threads_pipeline.threads_cli.reply.require_token", return_value="fake"):
        result = runner.invoke(app, ["reply", "unhide", "R_456", "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed == {"ok": True, "data": {"hidden": False, "reply_id": "R_456"}}
