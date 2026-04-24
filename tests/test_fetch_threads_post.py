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
