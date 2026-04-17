"""threads_cli/_backup.py 的 unit test。"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from threads_pipeline.threads_cli._backup import (
    save_delete_backup,
    BackupError,
)


def test_save_backup_creates_file(tmp_path):
    post_data = {"id": "POST_1", "text": "hello", "timestamp": "2026-04-17T00:00:00Z"}
    path = save_delete_backup(post_id="POST_1", post_data=post_data, backup_dir=tmp_path)
    assert path.exists()
    assert path.is_file()
    assert path.parent == tmp_path
    assert path.name.startswith("POST_1_")
    assert path.suffix == ".json"


def test_save_backup_content_has_metadata(tmp_path):
    post_data = {"id": "POST_1", "text": "hi"}
    path = save_delete_backup(post_id="POST_1", post_data=post_data, backup_dir=tmp_path)
    content = json.loads(path.read_text(encoding="utf-8"))
    assert content["post"] == post_data
    assert "captured_at" in content
    assert "T" in content["captured_at"]
    assert content["captured_before_delete"] is True


def test_save_backup_creates_dir_if_missing(tmp_path):
    target_dir = tmp_path / "nested" / "does_not_exist"
    assert not target_dir.exists()
    path = save_delete_backup(post_id="POST_1", post_data={"id": "POST_1"}, backup_dir=target_dir)
    assert target_dir.exists()
    assert path.exists()


def test_save_backup_timestamp_in_filename(tmp_path):
    import re
    path = save_delete_backup(post_id="POST_1", post_data={"id": "POST_1"}, backup_dir=tmp_path)
    assert re.match(r"POST_1_\d{8}-\d{6}\.json$", path.name)


def test_save_backup_raises_on_unwritable_dir(tmp_path):
    """PermissionError IS-A OSError，會被 except OSError 接到並包成 BackupError。"""
    with patch("threads_pipeline.threads_cli._backup.Path.write_text",
               side_effect=PermissionError("readonly fs")):
        with pytest.raises(BackupError) as exc_info:
            save_delete_backup(post_id="POST_1", post_data={"id": "POST_1"}, backup_dir=tmp_path)
    assert "readonly fs" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, PermissionError)


def test_save_backup_preserves_cjk(tmp_path):
    post_data = {"id": "POST_1", "text": "測試繁體中文"}
    path = save_delete_backup(post_id="POST_1", post_data=post_data, backup_dir=tmp_path)
    raw = path.read_text(encoding="utf-8")
    assert "測試繁體中文" in raw
