"""CLI tests for `threads profile` sub-app（lookup + posts）。

App Review 2026-04-23 本輪送審範圍的 profile_discovery 面向。endpoint pre-approval
鎖住，所以實際 CLI 行為（含錯誤碼對應）只能用 mock 驗證。
"""

import json
from unittest.mock import MagicMock, patch

import requests
from typer.testing import CliRunner

from threads_pipeline.threads_cli.cli import app

runner = CliRunner()


# ═════════════════════════════════════════════════════════════════════════
# lookup
# ═════════════════════════════════════════════════════════════════════════

def _fake_post(**overrides):
    base = {
        "id": "P1",
        "username": "alice",
        "text": "hello world",
        "permalink": "https://www.threads.com/@alice/post/TARGET",
        "timestamp": "2026-04-23T00:00:00Z",
    }
    base.update(overrides)
    return base


def test_profile_lookup_human_mode():
    fake = _fake_post()
    with patch("threads_pipeline.threads_cli.profile.resolve_post_by_url", return_value=fake), \
         patch("threads_pipeline.threads_cli.profile.require_token", return_value="TKN"):
        result = runner.invoke(app, [
            "profile", "lookup",
            "https://www.threads.com/@alice/post/TARGET",
        ])
    assert result.exit_code == 0, result.output
    assert "P1" in result.output
    assert "@alice" in result.output
    assert "hello world" in result.output


def test_profile_lookup_json_mode():
    fake = _fake_post()
    with patch("threads_pipeline.threads_cli.profile.resolve_post_by_url", return_value=fake), \
         patch("threads_pipeline.threads_cli.profile.require_token", return_value="TKN"):
        result = runner.invoke(app, [
            "profile", "lookup",
            "https://www.threads.com/@alice/post/TARGET",
            "--json",
        ])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["ok"] is True
    assert parsed["data"]["post"]["id"] == "P1"
    assert parsed["data"]["post"]["text"] == "hello world"


def test_profile_lookup_unsupported_url():
    """短格式 URL（無 username）→ ValueError → UNSUPPORTED_URL。"""
    with patch(
        "threads_pipeline.threads_cli.profile.resolve_post_by_url",
        side_effect=ValueError("URL must be in form ..."),
    ), patch("threads_pipeline.threads_cli.profile.require_token", return_value="TKN"):
        result = runner.invoke(app, [
            "profile", "lookup",
            "https://www.threads.com/t/SHORTONLY",
            "--json",
        ])
    assert result.exit_code == 1
    parsed = json.loads(result.output.strip().split("\n")[0])
    assert parsed["ok"] is False
    assert parsed["error"]["code"] == "UNSUPPORTED_URL"


def test_profile_lookup_post_not_found():
    """URL 解析 OK 但 shortcode 不在 recent posts → LookupError → POST_NOT_FOUND。"""
    with patch(
        "threads_pipeline.threads_cli.profile.resolve_post_by_url",
        side_effect=LookupError("Post shortcode `X` not found in `alice`'s ..."),
    ), patch("threads_pipeline.threads_cli.profile.require_token", return_value="TKN"):
        result = runner.invoke(app, [
            "profile", "lookup",
            "https://www.threads.com/@alice/post/X",
            "--json",
        ])
    assert result.exit_code == 1
    parsed = json.loads(result.output.strip().split("\n")[0])
    assert parsed["error"]["code"] == "POST_NOT_FOUND"


def test_profile_lookup_permission_required_on_400():
    """HTTP 400 with "does not exist" → PERMISSION_REQUIRED（pre-approval 預期情境）。"""
    fake_resp = MagicMock(spec=requests.Response)
    fake_resp.status_code = 400
    fake_resp.json.return_value = {
        "error": {
            "message": "Object with ID 'alice' does not exist, cannot be loaded due to missing permissions",
            "type": "THApiException",
            "code": 100,
        }
    }
    http_err = requests.exceptions.HTTPError(response=fake_resp)
    with patch(
        "threads_pipeline.threads_cli.profile.resolve_post_by_url",
        side_effect=http_err,
    ), patch("threads_pipeline.threads_cli.profile.require_token", return_value="TKN"):
        result = runner.invoke(app, [
            "profile", "lookup",
            "https://www.threads.com/@alice/post/TARGET",
            "--json",
        ])
    assert result.exit_code == 1
    parsed = json.loads(result.output.strip().split("\n")[0])
    assert parsed["error"]["code"] == "PERMISSION_REQUIRED"
    assert "does not exist" in parsed["error"]["message"]


def test_profile_lookup_generic_api_error():
    """其他 RequestException → API_ERROR。"""
    with patch(
        "threads_pipeline.threads_cli.profile.resolve_post_by_url",
        side_effect=requests.exceptions.ConnectionError("connection refused"),
    ), patch("threads_pipeline.threads_cli.profile.require_token", return_value="TKN"):
        result = runner.invoke(app, [
            "profile", "lookup",
            "https://www.threads.com/@alice/post/TARGET",
            "--json",
        ])
    assert result.exit_code == 1
    parsed = json.loads(result.output.strip().split("\n")[0])
    assert parsed["error"]["code"] == "API_ERROR"


# ═════════════════════════════════════════════════════════════════════════
# posts
# ═════════════════════════════════════════════════════════════════════════

def test_profile_posts_human_mode():
    fake = {
        "posts": [
            _fake_post(id="P1", text="first post"),
            _fake_post(id="P2", text="second"),
        ],
        "next_cursor": None,
    }
    with patch("threads_pipeline.threads_cli.profile.fetch_user_threads", return_value=fake), \
         patch("threads_pipeline.threads_cli.profile.require_token", return_value="TKN"):
        result = runner.invoke(app, ["profile", "posts", "alice"])
    assert result.exit_code == 0, result.output
    assert "P1" in result.output
    assert "P2" in result.output
    assert "@alice" in result.output


def test_profile_posts_strips_leading_at_sign():
    """使用者可能帶 `@alice`；fetch_user_threads 收到的應該是純 username。"""
    fake = {"posts": [], "next_cursor": None}
    with patch(
        "threads_pipeline.threads_cli.profile.fetch_user_threads",
        return_value=fake,
    ) as mock_fn, patch(
        "threads_pipeline.threads_cli.profile.require_token", return_value="TKN"
    ):
        runner.invoke(app, ["profile", "posts", "@alice"])
    mock_fn.assert_called_once()
    assert mock_fn.call_args.kwargs["username"] == "alice"


def test_profile_posts_json_mode_with_cursor():
    fake = {
        "posts": [_fake_post(id="P1")],
        "next_cursor": "NEXT_CUR",
    }
    with patch("threads_pipeline.threads_cli.profile.fetch_user_threads", return_value=fake), \
         patch("threads_pipeline.threads_cli.profile.require_token", return_value="TKN"):
        result = runner.invoke(app, ["profile", "posts", "alice", "--json"])
    # 用 {...} 切 JSON（stderr 可能被 CliRunner 合到 output）
    json_start = result.output.find("{")
    json_end = result.output.rfind("}")
    assert json_start >= 0, result.output
    parsed = json.loads(result.output[json_start:json_end + 1])
    assert parsed["ok"] is True
    assert parsed["data"]["username"] == "alice"
    assert parsed["data"]["posts"][0]["id"] == "P1"
    assert parsed["next_cursor"] == "NEXT_CUR"


def test_profile_posts_limit_clamped():
    fake = {"posts": [], "next_cursor": None}
    with patch(
        "threads_pipeline.threads_cli.profile.fetch_user_threads",
        return_value=fake,
    ) as mock_fn, patch(
        "threads_pipeline.threads_cli.profile.require_token", return_value="TKN"
    ):
        result = runner.invoke(app, [
            "profile", "posts", "alice", "--limit", "500", "--json",
        ])
    assert result.exit_code == 0
    assert mock_fn.call_args.kwargs["limit"] == 100
    json_start = result.output.find("{")
    json_end = result.output.rfind("}")
    parsed = json.loads(result.output[json_start:json_end + 1])
    assert any(w["code"] == "LIMIT_CLAMPED" for w in parsed.get("warnings", []))


def test_profile_posts_passes_cursor():
    fake = {"posts": [], "next_cursor": None}
    with patch(
        "threads_pipeline.threads_cli.profile.fetch_user_threads",
        return_value=fake,
    ) as mock_fn, patch(
        "threads_pipeline.threads_cli.profile.require_token", return_value="TKN"
    ):
        runner.invoke(app, ["profile", "posts", "alice", "--cursor", "CUR_PREV"])
    assert mock_fn.call_args.kwargs["cursor"] == "CUR_PREV"


def test_profile_posts_permission_required_on_400():
    """pre-approval 預期：HTTP 400 → PERMISSION_REQUIRED。"""
    fake_resp = MagicMock(spec=requests.Response)
    fake_resp.status_code = 400
    fake_resp.json.return_value = {
        "error": {
            "message": "Object with ID 'alice' does not exist, cannot be loaded due to missing permissions",
        }
    }
    http_err = requests.exceptions.HTTPError(response=fake_resp)
    with patch(
        "threads_pipeline.threads_cli.profile.fetch_user_threads",
        side_effect=http_err,
    ), patch("threads_pipeline.threads_cli.profile.require_token", return_value="TKN"):
        result = runner.invoke(app, ["profile", "posts", "alice", "--json"])
    assert result.exit_code == 1
    parsed = json.loads(result.output.strip().split("\n")[0])
    assert parsed["error"]["code"] == "PERMISSION_REQUIRED"


def test_profile_posts_empty_no_posts():
    fake = {"posts": [], "next_cursor": None}
    with patch("threads_pipeline.threads_cli.profile.fetch_user_threads", return_value=fake), \
         patch("threads_pipeline.threads_cli.profile.require_token", return_value="TKN"):
        result = runner.invoke(app, ["profile", "posts", "alice"])
    assert result.exit_code == 0
    assert "@alice" in result.output
    assert "尚無" in result.output or "no" in result.output.lower()
