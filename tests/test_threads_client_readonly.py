"""threads_client.py 的 B2 唯讀 helper unit test（mock requests）。"""

from unittest.mock import patch, MagicMock

import pytest

from threads_pipeline.threads_client import (
    fetch_account_info,
    fetch_account_insights_cli,
    list_my_posts,
    fetch_post_detail,
    fetch_post_insights_cli,
    fetch_post_replies,
)


def _mock_get(return_json: dict, status_code: int = 200):
    """Helper: 建一個 requests.get 的 mock。"""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = return_json
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# === fetch_account_info ===

def test_fetch_account_info_calls_me_endpoint():
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"id": "ME_123", "username": "foo"}
        result = fetch_account_info(token="TKN")
    args, kwargs = mock_req.call_args
    url = args[0]
    params = args[1]
    assert "/me" in url
    assert params["access_token"] == "TKN"
    assert "username" in params.get("fields", "")
    assert result == {"id": "ME_123", "username": "foo"}


# === fetch_account_insights_cli ===

def test_fetch_account_insights_cli_calls_threads_insights_endpoint():
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"data": [{"name": "views", "values": [{"value": 42}]}]}
        result = fetch_account_insights_cli(token="TKN")
    args, _ = mock_req.call_args
    url = args[0]
    assert "/me/threads_insights" in url
    assert isinstance(result, dict)
    assert "data" in result


# === list_my_posts ===

def test_list_my_posts_basic():
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {
            "data": [{"id": "P1"}, {"id": "P2"}],
            "paging": {"cursors": {"after": "CURSOR_ABC"}},
        }
        result = list_my_posts(token="TKN", limit=25)
    args, _ = mock_req.call_args
    params = args[1]
    assert params["limit"] == 25
    assert "after" not in params
    assert result["posts"] == [{"id": "P1"}, {"id": "P2"}]
    assert result["next_cursor"] == "CURSOR_ABC"


def test_list_my_posts_with_cursor():
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"data": [], "paging": {}}
        list_my_posts(token="TKN", limit=10, cursor="PREV_CURSOR")
    args, _ = mock_req.call_args
    params = args[1]
    assert params["after"] == "PREV_CURSOR"


def test_list_my_posts_no_next_cursor_when_empty_paging():
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"data": [{"id": "P1"}]}
        result = list_my_posts(token="TKN", limit=25)
    assert result["next_cursor"] is None


# === fetch_post_detail ===

def test_fetch_post_detail_basic():
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"id": "POST_1", "text": "hi", "timestamp": "2026-04-17T00:00:00Z"}
        result = fetch_post_detail(post_id="POST_1", token="TKN")
    args, _ = mock_req.call_args
    url = args[0]
    assert "POST_1" in url
    assert result["id"] == "POST_1"


def test_fetch_post_detail_custom_fields():
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"id": "POST_1"}
        fetch_post_detail(post_id="POST_1", token="TKN", fields="id,text,timestamp,media_type,permalink")
    args, _ = mock_req.call_args
    params = args[1]
    assert "media_type" in params["fields"]


# === fetch_post_insights_cli ===

def test_fetch_post_insights_cli():
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"data": [
            {"name": "views", "values": [{"value": 100}]},
            {"name": "likes", "values": [{"value": 5}]},
        ]}
        result = fetch_post_insights_cli(post_id="POST_1", token="TKN")
    args, _ = mock_req.call_args
    url = args[0]
    assert "/POST_1/insights" in url
    assert "data" in result


# === fetch_post_replies ===

def test_fetch_post_replies_basic():
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {
            "data": [{"id": "R1"}, {"id": "R2"}],
            "paging": {"cursors": {"after": "C1"}},
        }
        result = fetch_post_replies(post_id="POST_1", token="TKN", limit=25)
    args, _ = mock_req.call_args
    url = args[0]
    assert "/POST_1/replies" in url
    assert result["replies"] == [{"id": "R1"}, {"id": "R2"}]
    assert result["next_cursor"] == "C1"


def test_fetch_post_replies_with_cursor():
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"data": [], "paging": {}}
        fetch_post_replies(post_id="POST_1", token="TKN", limit=10, cursor="PREV")
    args, _ = mock_req.call_args
    params = args[1]
    assert params["after"] == "PREV"
