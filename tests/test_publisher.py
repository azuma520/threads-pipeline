"""publisher 模組測試（mock 所有 API 呼叫）。"""

from unittest.mock import patch, MagicMock

import pytest


def test_publish_text_success():
    """Step 1 建 container + Step 2 publish 成功。"""
    from threads_pipeline.publisher import publish_text

    mock_step1 = MagicMock()
    mock_step1.status_code = 200
    mock_step1.json.return_value = {"id": "CONTAINER_123"}

    mock_step2 = MagicMock()
    mock_step2.status_code = 200
    mock_step2.json.return_value = {"id": "POST_456"}

    with patch("threads_pipeline.publisher.requests.post", side_effect=[mock_step1, mock_step2]):
        post_id = publish_text("測試文字", token="fake_token")

    assert post_id == "POST_456"


def test_publish_text_step1_fail():
    """Step 1 失敗應 raise，不呼叫 step 2。"""
    from threads_pipeline.publisher import publish_text, PublishError

    mock_fail = MagicMock()
    mock_fail.status_code = 400
    mock_fail.json.return_value = {"error": {"message": "Invalid text"}}

    with patch("threads_pipeline.publisher.requests.post", return_value=mock_fail) as mocked:
        with pytest.raises(PublishError):
            publish_text("", token="fake_token")

    assert mocked.call_count == 1


def test_publish_text_step2_fail_orphan_container():
    """Step 2 失敗應在錯誤訊息包含 container_id（孤兒 container）。"""
    from threads_pipeline.publisher import publish_text, PublishError

    mock_step1 = MagicMock()
    mock_step1.status_code = 200
    mock_step1.json.return_value = {"id": "CONTAINER_999"}

    mock_step2 = MagicMock()
    mock_step2.status_code = 500
    mock_step2.json.return_value = {"error": {"message": "Server error"}}

    with patch("threads_pipeline.publisher.requests.post", side_effect=[mock_step1, mock_step2]):
        with pytest.raises(PublishError) as exc_info:
            publish_text("ok text", token="fake_token")

    assert "CONTAINER_999" in str(exc_info.value)


def test_publish_text_error_not_dict():
    """若 body['error'] 非 dict（如字串 / null），不該 AttributeError crash。"""
    from threads_pipeline.publisher import publish_text, PublishError

    mock_fail = MagicMock()
    mock_fail.status_code = 400
    mock_fail.json.return_value = {"error": "some raw string error"}

    with patch("threads_pipeline.publisher.requests.post", return_value=mock_fail):
        with pytest.raises(PublishError):
            publish_text("x", token="fake")


def test_publish_text_no_token_raises():
    """未傳 token 且 env 無 token 時 raise。"""
    from threads_pipeline.publisher import publish_text, PublishError

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(PublishError, match="TOKEN"):
            publish_text("x")


def test_reply_to_passes_reply_to_id():
    """reply_to 應把 post_id 傳成 reply_to_id 給 publish_text。"""
    from threads_pipeline.publisher import reply_to

    with patch("threads_pipeline.publisher.publish_text") as mock_pub:
        mock_pub.return_value = "REPLY_POST_789"
        result = reply_to("PARENT_POST_123", "我的回覆", token="fake")

    assert result == "REPLY_POST_789"
    mock_pub.assert_called_once_with(
        "我的回覆",
        token="fake",
        reply_to_id="PARENT_POST_123",
    )


def test_reply_to_requires_parent_id():
    """reply_to 不接受空 post_id。"""
    from threads_pipeline.publisher import reply_to, PublishError

    with pytest.raises(PublishError, match="post_id"):
        reply_to("", "text", token="fake")
