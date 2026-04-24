"""threads_client 測試：搜尋、去重、時間過濾、錯誤重試、Token 管理。"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests

from threads_pipeline.threads_client import (
    _request_with_retry,
    _search_keyword,
    fetch_posts,
    validate_token,
    refresh_token,
)


@pytest.fixture
def base_config():
    return {
        "threads": {
            "access_token": "test_token_123",
            "keywords": ["AI", "Claude"],
            "sort": "TOP",
            "max_posts_per_keyword": 25,
        }
    }


class TestFetchPosts:
    """fetch_posts 整合測試。"""

    @patch("threads_pipeline.threads_client._search_keyword")
    def test_normal_fetch(self, mock_search, base_config, mock_threads_response):
        """正常取得貼文。"""
        mock_search.return_value = mock_threads_response["data"][:3]
        posts = fetch_posts(base_config)
        assert len(posts) > 0
        assert all("id" in p for p in posts)

    @patch("threads_pipeline.threads_client._search_keyword")
    def test_dedup_across_keywords(self, mock_search, base_config):
        """跨關鍵字去重：同一篇貼文只保留一次。"""
        duplicate_post = {
            "id": "SAME_ID",
            "text": "test",
            "username": "user1",
            "timestamp": "2026-03-29T12:00:00+0000",
            "like_count": 10,
            "permalink": "https://threads.net/@user1/post/X",
        }
        mock_search.return_value = [duplicate_post]

        posts = fetch_posts(base_config)
        # 兩個 keyword 都搜到同一篇，但結果只有 1 篇
        assert len(posts) == 1
        assert posts[0]["id"] == "SAME_ID"

    @patch("threads_pipeline.threads_client._search_keyword")
    def test_empty_results(self, mock_search, base_config):
        """所有關鍵字都沒結果。"""
        mock_search.return_value = []
        posts = fetch_posts(base_config)
        assert posts == []

    @patch("threads_pipeline.threads_client._search_keyword")
    def test_keyword_error_skips_gracefully(self, mock_search, base_config):
        """某個關鍵字搜尋失敗，不影響其他。"""
        good_post = {
            "id": "GOOD_1",
            "text": "good",
            "username": "u",
            "timestamp": "2026-03-29T12:00:00+0000",
            "like_count": 5,
            "permalink": "https://threads.net/@u/post/G",
        }
        mock_search.side_effect = [
            Exception("API error"),  # 第一個 keyword 失敗
            [good_post],  # 第二個 keyword 成功
        ]

        posts = fetch_posts(base_config)
        assert len(posts) == 1
        assert posts[0]["id"] == "GOOD_1"


class TestSearchKeyword:
    """_search_keyword 單元測試。"""

    @patch("threads_pipeline.threads_client._request_with_retry")
    def test_returns_posts(self, mock_request):
        """正常回傳貼文列表。"""
        mock_request.return_value = {
            "data": [{"id": "1", "text": "hello"}]
        }
        result = _search_keyword("AI", "token123")
        assert len(result) == 1
        assert result[0]["id"] == "1"

    @patch("threads_pipeline.threads_client._request_with_retry")
    def test_respects_max_results(self, mock_request):
        """不超過 max_results。"""
        mock_request.return_value = {
            "data": [{"id": str(i)} for i in range(50)]
        }
        result = _search_keyword("AI", "token123", max_results=10)
        assert len(result) == 10


class TestRequestWithRetry:
    """_request_with_retry 重試邏輯。"""

    @patch("requests.Session.get")
    def test_success_on_first_try(self, mock_get):
        """第一次就成功。"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = _request_with_retry("http://test.com", {})
        assert result == {"data": []}
        assert mock_get.call_count == 1

    @patch("time.sleep")
    @patch("requests.Session.get")
    def test_retry_on_500(self, mock_get, mock_sleep):
        """500 錯誤觸發重試。"""
        fail_resp = MagicMock()
        fail_resp.status_code = 500
        fail_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("500")

        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"data": ["ok"]}
        ok_resp.raise_for_status = MagicMock()

        mock_get.side_effect = [fail_resp, ok_resp]

        result = _request_with_retry("http://test.com", {})
        assert result == {"data": ["ok"]}
        assert mock_get.call_count == 2

    @patch("time.sleep")
    @patch("requests.Session.get")
    def test_raises_after_max_retries(self, mock_get, mock_sleep):
        """超過最大重試次數後拋出例外。"""
        fail_resp = MagicMock()
        fail_resp.status_code = 500
        fail_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("500")
        mock_get.return_value = fail_resp

        with pytest.raises(requests.exceptions.HTTPError):
            _request_with_retry("http://test.com", {}, max_retries=3)

    @patch("time.sleep")
    @patch("requests.Session.get")
    def test_no_retry_on_4xx(self, mock_get, mock_sleep):
        """4xx 立刻拋出，不重試（避免 access_token 被多次 log 外洩）。"""
        fail_resp = MagicMock()
        fail_resp.status_code = 400
        http_err = requests.exceptions.HTTPError("400 Bad Request")
        http_err.response = fail_resp
        fail_resp.raise_for_status.side_effect = http_err
        mock_get.return_value = fail_resp

        with pytest.raises(requests.exceptions.HTTPError):
            _request_with_retry("http://test.com", {}, max_retries=3)

        assert mock_get.call_count == 1
        assert mock_sleep.call_count == 0


class TestValidateToken:
    """validate_token 測試。"""

    @patch("threads_pipeline.threads_client._request_with_retry")
    def test_validate_token_success(self, mock_request):
        """Token 有效時，回傳含 id 的使用者資料 dict。"""
        mock_request.return_value = {"id": "12345", "username": "test_user"}

        result = validate_token("valid_token_abc")

        assert result["id"] == "12345"
        assert result["username"] == "test_user"
        # 確認呼叫了正確的 API endpoint
        call_args = mock_request.call_args
        assert "/me" in call_args[0][0]
        assert call_args[0][1]["access_token"] == "valid_token_abc"

    @patch("threads_pipeline.threads_client._request_with_retry")
    def test_validate_token_invalid(self, mock_request):
        """Token 無效（API 回傳 400/401）時，raise Exception 且訊息有意義。"""
        mock_request.side_effect = requests.exceptions.HTTPError("400 Bad Request")

        with pytest.raises(Exception) as exc_info:
            validate_token("expired_or_invalid_token")

        assert "Token 無效或已過期" in str(exc_info.value)

    @patch("threads_pipeline.threads_client._request_with_retry")
    def test_validate_token_missing_id(self, mock_request):
        """回應格式異常（缺少 id）時，raise Exception。"""
        mock_request.return_value = {"error": "unexpected format"}

        with pytest.raises(Exception) as exc_info:
            validate_token("some_token")

        assert "id" in str(exc_info.value)


class TestRefreshToken:
    """refresh_token 測試。"""

    @patch("threads_pipeline.threads_client._request_with_retry")
    def test_refresh_token_success(self, mock_request):
        """Token 成功續期時，回傳新的 token 字串。"""
        mock_request.return_value = {
            "access_token": "new_token_xyz",
            "token_type": "bearer",
        }

        result = refresh_token("old_valid_token")

        assert result == "new_token_xyz"
        # 確認呼叫了正確的 API endpoint（不是 v1.0 底下）
        call_args = mock_request.call_args
        assert "refresh_access_token" in call_args[0][0]
        assert "v1.0" not in call_args[0][0]
        assert call_args[0][1]["grant_type"] == "th_refresh_token"

    @patch("threads_pipeline.threads_client._request_with_retry")
    def test_refresh_token_expired(self, mock_request):
        """Token 已完全過期（API 回傳 400）時，回傳 None 而非拋出例外。"""
        mock_request.side_effect = requests.exceptions.HTTPError("400 Bad Request")

        result = refresh_token("fully_expired_token")

        assert result is None
