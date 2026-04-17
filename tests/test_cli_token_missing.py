"""TOKEN_MISSING 和 INVALID_ARGS 的 JSON envelope 測試（B3 修正）。"""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from threads_pipeline.threads_cli.cli import app

runner = CliRunner()


# === TOKEN_MISSING in --json mode ===

def test_token_missing_json_emits_envelope():
    """--json + token missing → exit 1, envelope ok:false, code TOKEN_MISSING。"""
    with patch.dict("os.environ", {}, clear=False):
        with patch.dict("os.environ", {"THREADS_ACCESS_TOKEN": ""}):
            result = runner.invoke(app, ["account", "info", "--json"])
    assert result.exit_code == 1
    lines = [l for l in result.output.strip().split("\n") if l.strip()]
    parsed = json.loads(lines[0])
    assert parsed["ok"] is False
    assert parsed["error"]["code"] == "TOKEN_MISSING"


def test_token_missing_human_no_envelope():
    """無 --json + token missing → exit 1, stderr 有 [ERROR]，stdout 無 JSON。"""
    with patch.dict("os.environ", {}, clear=False):
        with patch.dict("os.environ", {"THREADS_ACCESS_TOKEN": ""}):
            result = runner.invoke(app, ["account", "info"])
    assert result.exit_code == 1
    assert "[ERROR]" in result.output
    assert '"ok"' not in result.output


def test_token_missing_posts_list_json():
    """posts list --json + token missing → envelope。"""
    with patch.dict("os.environ", {}, clear=False):
        with patch.dict("os.environ", {"THREADS_ACCESS_TOKEN": ""}):
            result = runner.invoke(app, ["posts", "list", "--json"])
    assert result.exit_code == 1
    lines = [l for l in result.output.strip().split("\n") if l.strip()]
    parsed = json.loads(lines[0])
    assert parsed["error"]["code"] == "TOKEN_MISSING"


def test_token_missing_delete_json():
    """post delete --json + token missing → envelope（dry-run 不需 token，但 --confirm --yes 需要）。

    注意：delete 在 dry-run 模式下 require_token 在 confirm 之前就跑。
    """
    with patch.dict("os.environ", {}, clear=False):
        with patch.dict("os.environ", {"THREADS_ACCESS_TOKEN": ""}):
            result = runner.invoke(app, ["post", "delete", "POST_1", "--json"])
    assert result.exit_code == 1
    lines = [l for l in result.output.strip().split("\n") if l.strip()]
    parsed = json.loads(lines[0])
    assert parsed["error"]["code"] == "TOKEN_MISSING"
