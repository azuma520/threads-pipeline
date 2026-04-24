"""threads_client profile_discovery helper 單元測試。

endpoint 在 `threads_profile_discovery` 核准前完全鎖住，此處 unit tests 全 mock
`_request_with_retry`，僅驗證 URL 組法、參數、回傳 shape、URL parser 邊界。
"""

import pytest
from unittest.mock import patch

from threads_pipeline.threads_client import (
    fetch_user_profile,
    fetch_user_threads,
    parse_threads_post_url,
    resolve_post_by_url,
)


# ─── fetch_user_profile ───────────────────────────────────────────────

def test_fetch_user_profile_calls_username_endpoint():
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"id": "U1", "username": "alice"}
        result = fetch_user_profile(username="alice", token="TKN")

    url, params = mock_req.call_args[0]
    assert url.endswith("/alice")
    assert params["access_token"] == "TKN"
    fields = params.get("fields", "")
    for required in ("id", "username", "threads_biography"):
        assert required in fields, f"fields missing {required}: {fields}"
    assert result == {"id": "U1", "username": "alice"}


# ─── fetch_user_threads ───────────────────────────────────────────────

def test_fetch_user_threads_basic():
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {
            "data": [{"id": "P1", "text": "hi"}, {"id": "P2"}],
            "paging": {"cursors": {"after": "CUR1"}},
        }
        result = fetch_user_threads(username="alice", token="TKN", limit=25)

    url, params = mock_req.call_args[0]
    assert url.endswith("/alice/threads")
    assert params["access_token"] == "TKN"
    assert params["limit"] == 25
    assert "after" not in params
    assert result["posts"] == [{"id": "P1", "text": "hi"}, {"id": "P2"}]
    assert result["next_cursor"] == "CUR1"


def test_fetch_user_threads_with_cursor():
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"data": [], "paging": {}}
        fetch_user_threads(username="alice", token="TKN", limit=10, cursor="PREV")

    params = mock_req.call_args[0][1]
    assert params["after"] == "PREV"


def test_fetch_user_threads_requests_text_field():
    """fields 必須含 text（這是 user 要的「URL → 讀內文」核心欄位）。"""
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"data": [], "paging": {}}
        fetch_user_threads(username="alice", token="TKN")

    fields = mock_req.call_args[0][1].get("fields", "")
    for required in ("id", "text", "permalink", "timestamp"):
        assert required in fields, f"fields missing {required}: {fields}"


def test_fetch_user_threads_no_cursor_when_missing():
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"data": [{"id": "P1"}]}
        result = fetch_user_threads(username="alice", token="TKN")
    assert result["next_cursor"] is None


# ─── parse_threads_post_url ───────────────────────────────────────────

@pytest.mark.parametrize("url,expected", [
    (
        "https://www.threads.com/@lin__photograph/post/DXYP5WymvIs",
        ("lin__photograph", "DXYP5WymvIs"),
    ),
    (
        "https://threads.com/@alice/post/ABCDEF",
        ("alice", "ABCDEF"),
    ),
    (
        "https://www.threads.net/@bob/post/XyZ_123",
        ("bob", "XyZ_123"),
    ),
    (
        "http://www.threads.com/@user/post/SHORT/",
        ("user", "SHORT"),
    ),
    (
        "https://www.threads.com/@user/post/SHORT?utm_source=x",
        ("user", "SHORT"),
    ),
    (
        "HTTPS://WWW.THREADS.COM/@user/post/SHORT",
        ("user", "SHORT"),
    ),
])
def test_parse_threads_post_url_accepts(url, expected):
    assert parse_threads_post_url(url) == expected


@pytest.mark.parametrize("url", [
    "https://www.threads.com/t/XYZ",              # 短格式，無 username
    "https://www.threads.com/@user/",              # 無 post segment
    "https://www.threads.com/@user/post/",         # shortcode 空
    "https://instagram.com/@user/post/XYZ",        # 非 threads 域名
    "not a url",
    "",
])
def test_parse_threads_post_url_rejects(url):
    with pytest.raises(ValueError):
        parse_threads_post_url(url)


# ─── resolve_post_by_url ──────────────────────────────────────────────

def test_resolve_post_by_url_matches_shortcode_in_permalink():
    """resolve_post_by_url 要能從 user recent posts 中匹配到 shortcode。"""
    fake_posts = [
        {"id": "P1", "permalink": "https://www.threads.com/@alice/post/OTHER1", "text": "a"},
        {"id": "P2", "permalink": "https://www.threads.com/@alice/post/TARGET", "text": "hit"},
        {"id": "P3", "permalink": "https://www.threads.com/@alice/post/OTHER2", "text": "c"},
    ]
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"data": fake_posts, "paging": {}}
        result = resolve_post_by_url(
            url="https://www.threads.com/@alice/post/TARGET",
            token="TKN",
        )
    assert result["id"] == "P2"
    assert result["text"] == "hit"


def test_resolve_post_by_url_raises_lookup_when_not_in_recent():
    """shortcode 不在最近 N 則貼文 → LookupError。"""
    fake_posts = [
        {"id": "P1", "permalink": "https://www.threads.com/@alice/post/X1"},
        {"id": "P2", "permalink": "https://www.threads.com/@alice/post/X2"},
    ]
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"data": fake_posts, "paging": {}}
        with pytest.raises(LookupError) as exc:
            resolve_post_by_url(
                url="https://www.threads.com/@alice/post/MISSING",
                token="TKN",
            )
    assert "MISSING" in str(exc.value)


def test_resolve_post_by_url_raises_value_error_on_bad_url():
    """短格式 URL（無 username）無法用 profile_discovery 解析。"""
    with pytest.raises(ValueError):
        resolve_post_by_url(
            url="https://www.threads.com/t/XYZ",
            token="TKN",
        )


def test_resolve_post_by_url_calls_user_threads_endpoint():
    """resolve_post_by_url 應透過 /{username}/threads 查（非直接呼 /{post_id}）。"""
    fake_posts = [
        {"id": "P1", "permalink": "https://www.threads.com/@alice/post/TARGET", "text": "ok"},
    ]
    with patch("threads_pipeline.threads_client._request_with_retry") as mock_req:
        mock_req.return_value = {"data": fake_posts, "paging": {}}
        resolve_post_by_url(
            url="https://www.threads.com/@alice/post/TARGET",
            token="TKN",
        )
    url = mock_req.call_args[0][0]
    assert url.endswith("/alice/threads")
