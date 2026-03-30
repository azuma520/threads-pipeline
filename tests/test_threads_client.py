"""threads_client 測試：搜尋、去重、時間過濾、錯誤重試。"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests

from threads_pipeline.threads_client import (
    _request_with_retry,
    _search_keyword,
    fetch_posts,
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
