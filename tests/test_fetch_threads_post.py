"""Unit tests for scripts/fetch_threads_post.py pure functions."""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

# script 不在 package，走路徑 import
_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import fetch_threads_post as ftp  # noqa: E402  # pyright: ignore[reportMissingImports]


class TestParseUrl:
    def test_standard_com_url(self):
        assert ftp.parse_url(
            "https://www.threads.com/@kanisleo328/post/DXO2PlPEoOQ"
        ) == ("kanisleo328", "DXO2PlPEoOQ")

    def test_threads_net_domain(self):
        assert ftp.parse_url(
            "https://www.threads.net/@user_name/post/ABC123"
        ) == ("user_name", "ABC123")

    def test_with_query_string(self):
        assert ftp.parse_url(
            "https://www.threads.com/@foo.bar/post/XYZ?igsh=abc"
        ) == ("foo.bar", "XYZ")

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            ftp.parse_url("https://example.com/not-threads")


class TestClassify:
    MAIN = "kanisleo328"

    def _mk(self, is_reply, author, reply_to=None):
        # Schema 實測：is_reply / reply_to_author 皆巢在 text_post_app_info 裡。
        info = {"is_reply": is_reply}
        if reply_to:
            info["reply_to_author"] = {"username": reply_to}
        return {
            "user": {"username": author},
            "text_post_app_info": info,
        }

    def test_a_main_post(self):
        assert ftp.classify(self._mk(False, self.MAIN), self.MAIN) == "A"

    def test_b_author_thread_extension(self):
        assert ftp.classify(self._mk(True, self.MAIN, self.MAIN), self.MAIN) == "B"

    def test_c_author_replies_commenter(self):
        assert ftp.classify(self._mk(True, self.MAIN, "someone_else"), self.MAIN) == "C"

    def test_d_other_user_top_level_reply(self):
        assert ftp.classify(self._mk(True, "bob", self.MAIN), self.MAIN) == "D"

    def test_e_deep_reply(self):
        assert ftp.classify(self._mk(True, "bob", "alice"), self.MAIN) == "E"

    def test_missing_reply_to_author_treated_as_e(self):
        # is_reply=True but no reply_to_author → cannot classify → E
        post = {
            "user": {"username": "bob"},
            "text_post_app_info": {"is_reply": True},
        }
        assert ftp.classify(post, self.MAIN) == "E"

    def test_missing_is_reply_key_treated_as_a(self):
        # I5: commit to prototype behavior — absent is_reply → "A"（與明文 False 同）。
        # 包含 text_post_app_info 不存在、或存在但缺 is_reply 兩種情境。
        assert ftp.classify({"user": {"username": self.MAIN}}, self.MAIN) == "A"
        assert ftp.classify(
            {"user": {"username": self.MAIN}, "text_post_app_info": {}},
            self.MAIN,
        ) == "A"
