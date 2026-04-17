"""threads account info / insights 指令的 CliRunner 測試。"""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from threads_pipeline.threads_cli.cli import app

runner = CliRunner()


# === account info ===

def test_account_info_human_mode():
    """人類模式：stdout 含欄位 label。"""
    with patch("threads_pipeline.threads_cli.account.fetch_account_info",
               return_value={"id": "ME_123", "username": "azuma"}), \
         patch("threads_pipeline.threads_cli.account.require_token", return_value="fake"):
        result = runner.invoke(app, ["account", "info"])
    assert result.exit_code == 0
    assert "ME_123" in result.output
    assert "azuma" in result.output


def test_account_info_json_mode():
    """JSON 模式：stdout 是合法 envelope。"""
    with patch("threads_pipeline.threads_cli.account.fetch_account_info",
               return_value={"id": "ME_123", "username": "azuma"}), \
         patch("threads_pipeline.threads_cli.account.require_token", return_value="fake"):
        result = runner.invoke(app, ["account", "info", "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed == {"ok": True, "data": {"id": "ME_123", "username": "azuma"}}


def test_account_info_api_error_json_mode():
    """API error → exit 1, envelope ok:false。"""
    import requests
    err = requests.exceptions.RequestException("network down")
    with patch("threads_pipeline.threads_cli.account.fetch_account_info", side_effect=err), \
         patch("threads_pipeline.threads_cli.account.require_token", return_value="fake"):
        result = runner.invoke(app, ["account", "info", "--json"])
    assert result.exit_code == 1
    # stdout 應含 error envelope（可能有末尾換行）
    parsed = json.loads(result.output.strip().split("\n")[0])
    assert parsed["ok"] is False
    assert parsed["error"]["code"] == "API_ERROR"


# === account insights ===

def test_account_insights_human_mode():
    """人類模式：stdout 含 metric 名稱。"""
    with patch("threads_pipeline.threads_cli.account.fetch_account_insights_cli",
               return_value={"data": [
                   {"name": "views", "values": [{"value": 1234}]},
                   {"name": "likes", "values": [{"value": 56}]},
               ]}), \
         patch("threads_pipeline.threads_cli.account.require_token", return_value="fake"):
        result = runner.invoke(app, ["account", "insights"])
    assert result.exit_code == 0
    assert "views" in result.output
    assert "1234" in result.output


def test_account_insights_json_mode():
    """JSON 模式：envelope 保留 API 結構。"""
    fake_data = {"data": [{"name": "views", "values": [{"value": 42}]}]}
    with patch("threads_pipeline.threads_cli.account.fetch_account_insights_cli",
               return_value=fake_data), \
         patch("threads_pipeline.threads_cli.account.require_token", return_value="fake"):
        result = runner.invoke(app, ["account", "insights", "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed == {"ok": True, "data": fake_data}
