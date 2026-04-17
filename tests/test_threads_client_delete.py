"""threads_client.delete_post 的 unit test（mock requests.delete）。"""

from unittest.mock import patch, MagicMock

import pytest
import requests

from threads_pipeline.threads_client import delete_post


def test_delete_post_success():
    """200 response → return True。"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"success": True}
    mock_resp.raise_for_status = MagicMock()
    with patch("threads_pipeline.threads_client.requests.delete", return_value=mock_resp) as mock_del:
        result = delete_post(post_id="POST_1", token="TKN")
    assert result is True
    args, kwargs = mock_del.call_args
    url = args[0]
    assert "POST_1" in url
    assert kwargs["params"]["access_token"] == "TKN"


def test_delete_post_404_raises():
    """404 → raise HTTPError。"""
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    http_err = requests.exceptions.HTTPError(response=mock_resp)
    mock_resp.raise_for_status = MagicMock(side_effect=http_err)
    with patch("threads_pipeline.threads_client.requests.delete", return_value=mock_resp):
        with pytest.raises(requests.exceptions.HTTPError):
            delete_post(post_id="POST_1", token="TKN")


def test_delete_post_network_error_raises():
    """網路錯誤 → raise RequestException。"""
    with patch("threads_pipeline.threads_client.requests.delete",
               side_effect=requests.exceptions.ConnectionError("dns fail")):
        with pytest.raises(requests.exceptions.ConnectionError):
            delete_post(post_id="POST_1", token="TKN")
