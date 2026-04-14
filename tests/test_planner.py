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


class TestExtractFrameworkSection:
    @pytest.fixture
    def sample_md(self):
        return """# 爆款文案腳本 16+1 結構

## 結構總覽

| # | 名稱 | 公式 | 適用場景 |
|---|------|-----|---------|
| 01 | 引爆行動 | 觀點 → 危害 → 論據 → 結論 | 想改變讀者行為 |
| 11 | 逆襲引流 | 積極結果 → 獲得感 → 方案 → 互動結尾 | 分享成功經驗 |
| 15 | 通用類 | 鉤子開頭 → 塑造期待 → 解決方案 → 結尾 | 萬用結構 |

## 4 類結尾
| 類型 | 特點 |
|------|------|
| 互動式 | 引導留言 |
"""

    def test_extract_by_id(self, sample_md):
        from threads_pipeline.planner import extract_framework_section
        out = extract_framework_section(sample_md, 11)
        assert "逆襲引流" in out
        assert "積極結果" in out
        assert "分享成功經驗" in out

    def test_extract_by_name(self, sample_md):
        from threads_pipeline.planner import extract_framework_section
        out = extract_framework_section(sample_md, "逆襲引流")
        assert "11" in out
        assert "積極結果" in out

    def test_unknown_returns_none(self, sample_md):
        from threads_pipeline.planner import extract_framework_section
        assert extract_framework_section(sample_md, 99) is None
        assert extract_framework_section(sample_md, "不存在") is None

    def test_list_all_frameworks(self, sample_md):
        from threads_pipeline.planner import list_frameworks
        result = list_frameworks(sample_md)
        assert len(result) == 3
        ids = [fw["id"] for fw in result]
        assert 1 in ids and 11 in ids and 15 in ids
        fw11 = next(fw for fw in result if fw["id"] == 11)
        assert fw11["name"] == "逆襲引流"
        assert "積極結果" in fw11["formula"]
        assert "分享成功經驗" in fw11["when_to_use"]
