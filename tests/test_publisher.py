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


def test_publish_chain_success_3_posts():
    """3 則串文：第 1 則用 publish，後續 reply 到前一則（階梯式）。"""
    from threads_pipeline.publisher import publish_chain

    with patch("threads_pipeline.publisher.publish_text") as mock_pub, \
         patch("threads_pipeline.publisher.reply_to") as mock_rep:
        mock_pub.return_value = "POST_1"
        mock_rep.side_effect = ["POST_2", "POST_3"]

        ids = publish_chain(["第 1 則", "第 2 則", "第 3 則"], token="fake")

    assert ids == ["POST_1", "POST_2", "POST_3"]
    mock_pub.assert_called_once_with("第 1 則", token="fake")
    # 第 2 則 reply 到 POST_1
    assert mock_rep.call_args_list[0].args == ("POST_1", "第 2 則")
    # 第 3 則 reply 到 POST_2（階梯式，不是都 reply 到 POST_1）
    assert mock_rep.call_args_list[1].args == ("POST_2", "第 3 則")


def test_publish_chain_preflight_length_all_or_nothing():
    """任一則超過 500 字元 → 拒絕整串，零 API 呼叫。"""
    from threads_pipeline.publisher import publish_chain, PublishError

    with patch("threads_pipeline.publisher.publish_text") as mock_pub, \
         patch("threads_pipeline.publisher.reply_to") as mock_rep:
        with pytest.raises(PublishError, match="500"):
            publish_chain(["ok", "x" * 501, "ok"], token="fake")

    assert mock_pub.call_count == 0
    assert mock_rep.call_count == 0


def test_publish_chain_boundary_500_chars_ok():
    """剛好 500 字元應可通過 pre-flight（邊界正確性）。"""
    from threads_pipeline.publisher import publish_chain

    with patch("threads_pipeline.publisher.publish_text", return_value="POST_1"):
        result = publish_chain(["x" * 500], token="fake")
    assert result == ["POST_1"]


def test_publish_chain_opener_failure_raises_plain_publisherror():
    """第 1 則就失敗 → 拋 plain PublishError，不是 ChainMidwayError。

    理由：沒有 '已發' 需要回報，語義上不是 midway。
    """
    from threads_pipeline.publisher import publish_chain, PublishError, ChainMidwayError

    with patch("threads_pipeline.publisher.publish_text", side_effect=PublishError("opener fail")):
        with pytest.raises(PublishError) as exc_info:
            publish_chain(["a", "b", "c"], token="fake")

    # 必須是 plain PublishError，不是 ChainMidwayError
    assert not isinstance(exc_info.value, ChainMidwayError)


def test_publish_chain_midway_failure_reports_posted_ids():
    """第 3 則失敗 → ChainMidwayError 含已發的 IDs。"""
    from threads_pipeline.publisher import publish_chain, PublishError, ChainMidwayError

    with patch("threads_pipeline.publisher.publish_text") as mock_pub, \
         patch("threads_pipeline.publisher.reply_to") as mock_rep:
        mock_pub.return_value = "POST_1"
        mock_rep.side_effect = ["POST_2", PublishError("API 500")]

        with pytest.raises(ChainMidwayError) as exc_info:
            publish_chain(["a", "b", "c"], token="fake")

    assert exc_info.value.posted_ids == ["POST_1", "POST_2"]
    assert exc_info.value.failed_index == 2
    assert "API 500" in str(exc_info.value.cause)


def test_publish_chain_on_failure_retry_not_implemented():
    """on_failure=retry 應 raise NotImplementedError。"""
    from threads_pipeline.publisher import publish_chain

    with pytest.raises(NotImplementedError, match="retry"):
        publish_chain(["a"], token="fake", on_failure="retry")


def test_publish_chain_on_failure_rollback_not_implemented():
    """on_failure=rollback 應 raise NotImplementedError。"""
    from threads_pipeline.publisher import publish_chain

    with pytest.raises(NotImplementedError, match="rollback"):
        publish_chain(["a"], token="fake", on_failure="rollback")


def test_publish_chain_empty_list():
    """空清單應拒絕。"""
    from threads_pipeline.publisher import publish_chain, PublishError

    with pytest.raises(PublishError, match="empty"):
        publish_chain([], token="fake")
