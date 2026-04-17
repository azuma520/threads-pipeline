"""threads post delete 指令的 CliRunner 測試——涵蓋所有 path。"""

import json
from unittest.mock import patch, MagicMock

import requests
from typer.testing import CliRunner

from threads_pipeline.threads_cli.cli import app

runner = CliRunner()


# === dry-run (no --confirm) ===

def test_delete_dry_run_no_api_calls():
    """Dry-run 不應呼叫 GET / DELETE / 備份——零副作用。"""
    with patch("threads_pipeline.threads_cli.post.fetch_post_detail") as mock_get, \
         patch("threads_pipeline.threads_cli.post.delete_post") as mock_del, \
         patch("threads_pipeline.threads_cli.post.save_delete_backup") as mock_backup, \
         patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, ["post", "delete", "POST_1"])
    assert result.exit_code == 0
    assert "DRY RUN" in result.output
    assert "POST_1" in result.output
    assert mock_get.call_count == 0
    assert mock_del.call_count == 0
    assert mock_backup.call_count == 0


def test_delete_dry_run_json_mode():
    """Dry-run + --json 應吐 envelope，包含 dry_run: true。"""
    with patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, ["post", "delete", "POST_1", "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["ok"] is True
    assert parsed["data"]["dry_run"] is True
    assert parsed["data"]["post_id"] == "POST_1"


# === flag combo errors ===

def test_delete_yes_without_confirm_exit_2():
    """--yes 無 --confirm → exit 2。"""
    with patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, ["post", "delete", "POST_1", "--yes"])
    assert result.exit_code == 2


# === happy path: GET → backup → DELETE all succeed ===

def test_delete_confirm_yes_happy_path(tmp_path):
    """GET + backup + DELETE 全成功 → exit 0, 印備份路徑。"""
    fake_post = {"id": "POST_1", "text": "bye", "timestamp": "2026-04-17T00:00:00Z"}
    fake_backup_path = tmp_path / "POST_1_20260417-120000.json"

    with patch("threads_pipeline.threads_cli.post.fetch_post_detail",
               return_value=fake_post) as mock_get, \
         patch("threads_pipeline.threads_cli.post.save_delete_backup",
               return_value=fake_backup_path) as mock_backup, \
         patch("threads_pipeline.threads_cli.post.delete_post",
               return_value=True) as mock_del, \
         patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, ["post", "delete", "POST_1", "--confirm", "--yes"])

    assert result.exit_code == 0
    assert mock_get.call_count == 1
    assert mock_backup.call_count == 1
    assert mock_del.call_count == 1
    assert str(fake_backup_path) in result.output
    assert "[OK]" in result.output


# === backup failure: must NOT call DELETE ===

def test_delete_backup_failed_does_not_call_delete():
    """備份失敗 → 不呼叫 DELETE, exit 1, BACKUP_FAILED。"""
    from threads_pipeline.threads_cli._backup import BackupError
    with patch("threads_pipeline.threads_cli.post.fetch_post_detail",
               return_value={"id": "POST_1"}), \
         patch("threads_pipeline.threads_cli.post.save_delete_backup",
               side_effect=BackupError("disk full")), \
         patch("threads_pipeline.threads_cli.post.delete_post") as mock_del, \
         patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, ["post", "delete", "POST_1", "--confirm", "--yes", "--json"])
    assert result.exit_code == 1
    assert mock_del.call_count == 0
    parsed = json.loads(result.output.strip().split("\n")[0])
    assert parsed["ok"] is False
    assert parsed["error"]["code"] == "BACKUP_FAILED"


# === delete failure: backup preserved ===

def test_delete_api_failed_backup_preserved(tmp_path):
    """DELETE 失敗 → exit 1, DELETE_FAILED, 備份路徑仍出現在 stderr。"""
    fake_backup_path = tmp_path / "POST_1_20260417-120000.json"
    fake_backup_path.touch()

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    http_err = requests.exceptions.HTTPError(response=mock_resp)

    with patch("threads_pipeline.threads_cli.post.fetch_post_detail",
               return_value={"id": "POST_1"}), \
         patch("threads_pipeline.threads_cli.post.save_delete_backup",
               return_value=fake_backup_path), \
         patch("threads_pipeline.threads_cli.post.delete_post",
               side_effect=http_err), \
         patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, ["post", "delete", "POST_1", "--confirm", "--yes", "--json"])
    assert result.exit_code == 1
    parsed = json.loads(result.output.strip().split("\n")[0])
    assert parsed["error"]["code"] == "DELETE_FAILED"
    assert fake_backup_path.exists()


# === GET failure ===

def test_delete_get_detail_failed_exit_1():
    """GET /{post_id} 失敗（404）→ exit 1, NOT_FOUND, 不進備份/DELETE。"""
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    http_err = requests.exceptions.HTTPError(response=mock_resp)
    with patch("threads_pipeline.threads_cli.post.fetch_post_detail",
               side_effect=http_err), \
         patch("threads_pipeline.threads_cli.post.save_delete_backup") as mock_backup, \
         patch("threads_pipeline.threads_cli.post.delete_post") as mock_del, \
         patch("threads_pipeline.threads_cli.post.require_token", return_value="fake"):
        result = runner.invoke(app, ["post", "delete", "NONEXISTENT", "--confirm", "--yes", "--json"])
    assert result.exit_code == 1
    assert mock_backup.call_count == 0
    assert mock_del.call_count == 0
    parsed = json.loads(result.output.strip().split("\n")[0])
    assert parsed["error"]["code"] == "NOT_FOUND"
