"""threads_client.hide_reply 單元測試（mock requests.post）。"""

from unittest.mock import patch, MagicMock

from threads_pipeline.threads_client import hide_reply


def test_hide_reply_sends_hide_true():
    """hide=True 應呼叫 POST /{reply_id}/manage_reply 且 hide=true。"""
    fake_resp = MagicMock()
    fake_resp.raise_for_status.return_value = None
    fake_resp.json.return_value = {"success": True}
    with patch("threads_pipeline.threads_client.requests.post", return_value=fake_resp) as mock_post:
        result = hide_reply(reply_id="R_123", token="TKN", hide=True)
    args, kwargs = mock_post.call_args
    url = args[0]
    assert "/R_123/manage_reply" in url
    assert kwargs["params"]["access_token"] == "TKN"
    assert kwargs["params"]["hide"] == "true"
    assert result is True


def test_hide_reply_sends_hide_false():
    """hide=False 應傳 hide=false。"""
    fake_resp = MagicMock()
    fake_resp.raise_for_status.return_value = None
    fake_resp.json.return_value = {"success": True}
    with patch("threads_pipeline.threads_client.requests.post", return_value=fake_resp) as mock_post:
        hide_reply(reply_id="R_123", token="TKN", hide=False)
    _, kwargs = mock_post.call_args
    assert kwargs["params"]["hide"] == "false"


def test_hide_reply_raises_on_http_error():
    """HTTP 4xx/5xx 應 raise。"""
    import requests
    fake_resp = MagicMock()
    fake_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
    with patch("threads_pipeline.threads_client.requests.post", return_value=fake_resp):
        try:
            hide_reply(reply_id="R_404", token="TKN", hide=True)
            assert False, "should have raised"
        except requests.exceptions.HTTPError:
            pass
