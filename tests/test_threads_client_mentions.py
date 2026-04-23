"""threads_client.list_mentions 單元測試。"""

from unittest.mock import patch

from threads_pipeline.threads_client import list_mentions


def test_list_mentions_basic():
    """基本呼叫：GET /me/threads_mentions，回傳 {mentions, next_cursor}。"""
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {
            "data": [{"id": "M1", "text": "@you look at this"}, {"id": "M2"}],
            "paging": {"cursors": {"after": "CUR_ABC"}},
        }
        result = list_mentions(token="TKN", limit=25)
    args, _ = mock_req.call_args
    url = args[0]
    params = args[1]
    assert "/me/threads_mentions" in url
    assert params["access_token"] == "TKN"
    assert params["limit"] == 25
    assert "after" not in params
    assert result["mentions"] == [{"id": "M1", "text": "@you look at this"}, {"id": "M2"}]
    assert result["next_cursor"] == "CUR_ABC"


def test_list_mentions_with_cursor():
    """傳 cursor 時應放在 after 參數。"""
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"data": [], "paging": {}}
        list_mentions(token="TKN", limit=10, cursor="PREV")
    _, _ = mock_req.call_args
    params = mock_req.call_args[0][1]
    assert params["after"] == "PREV"


def test_list_mentions_no_next_cursor_when_paging_missing():
    """空 paging 應 next_cursor = None。"""
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"data": [{"id": "M1"}]}
        result = list_mentions(token="TKN", limit=25)
    assert result["next_cursor"] is None


def test_list_mentions_requests_expected_fields():
    """fields 參數應包含 id / text / username / timestamp。"""
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"data": [], "paging": {}}
        list_mentions(token="TKN", limit=25)
    params = mock_req.call_args[0][1]
    fields = params.get("fields", "")
    for required in ("id", "text", "username", "timestamp"):
        assert required in fields, f"fields missing {required}: {fields}"
