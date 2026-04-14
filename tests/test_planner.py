"""planner 測試。"""

import pytest


class TestSlugify:
    def test_chinese_only(self):
        from threads_pipeline.planner import slugify
        assert slugify("我學 Claude Code 一個月的心得") == "我學-claude-code-一個月的心"

    def test_strips_illegal_chars(self):
        from threads_pipeline.planner import slugify
        # Windows 檔名不合法字元
        assert slugify('題目/含*特殊?字元"<>|') == "題目含特殊字元"

    def test_truncates_over_20_chars(self):
        from threads_pipeline.planner import slugify
        topic = "這是一個超過二十個字元的非常冗長的題目用來測試截斷行為是否正確"
        result = slugify(topic)
        assert len(result) <= 20

    def test_lowercases_english(self):
        from threads_pipeline.planner import slugify
        assert "claude-code" in slugify("Claude Code")

    def test_empty_or_all_special_returns_timestamp_slug(self, monkeypatch):
        from threads_pipeline import planner
        class _DT:
            @staticmethod
            def now(tz=None):
                import datetime
                return datetime.datetime(2026, 4, 14, 10, 30, tzinfo=datetime.timezone.utc)
        monkeypatch.setattr(planner, "datetime", _DT)
        assert planner.slugify("///***???") == "plan-20260414-1030"
        assert planner.slugify("") == "plan-20260414-1030"

    def test_multiple_spaces_collapse(self):
        from threads_pipeline.planner import slugify
        assert slugify("hello    world") == "hello-world"
