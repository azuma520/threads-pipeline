"""report 測試：分組排序、零貼文、檔案寫入。"""

import os
import tempfile

import pytest

from threads_pipeline.report import _group_and_sort, render_report, save_report


@pytest.fixture
def report_config():
    return {
        "threads": {
            "keywords": ["AI", "LLM", "Claude"],
        },
        "anthropic": {
            "model": "claude-sonnet-4-6",
        },
        "output": {
            "directory": "",  # 測試時動態設定
        },
    }


class TestGroupAndSort:
    """_group_and_sort 測試。"""

    def test_groups_by_category(self, analyzed_posts):
        """按分類正確分組。"""
        grouped = _group_and_sort(analyzed_posts)
        categories = list(grouped.keys())
        # 應包含有貼文的分類
        assert "產業動態" in categories
        assert "新工具" in categories

    def test_category_order(self, analyzed_posts):
        """分類按指定順序排列。"""
        grouped = _group_and_sort(analyzed_posts)
        categories = list(grouped.keys())
        expected_order = ["新工具", "產業動態", "教學", "觀點"]
        # 過濾出有貼文的分類，確認相對順序正確
        filtered = [c for c in expected_order if c in categories]
        assert categories == filtered

    def test_sorted_by_score_desc(self, analyzed_posts):
        """組內按分數降序。"""
        grouped = _group_and_sort(analyzed_posts)
        for cat, posts in grouped.items():
            scores = [p["score"] for p in posts]
            assert scores == sorted(scores, reverse=True)

    def test_empty_posts(self):
        """空列表回傳空 dict。"""
        grouped = _group_and_sort([])
        assert len(grouped) == 0


class TestRenderReport:
    """render_report 測試。"""

    def test_contains_date(self, analyzed_posts, report_config):
        """報告包含日期。"""
        content = render_report(analyzed_posts, "2026-03-30", report_config)
        assert "2026-03-30" in content

    def test_contains_categories(self, analyzed_posts, report_config):
        """報告包含分類標題。"""
        content = render_report(analyzed_posts, "2026-03-30", report_config)
        assert "## 產業動態" in content
        assert "## 新工具" in content

    def test_contains_post_count(self, analyzed_posts, report_config):
        """報告包含貼文數量。"""
        content = render_report(analyzed_posts, "2026-03-30", report_config)
        assert "5 篇" in content

    def test_zero_posts_message(self, report_config):
        """零貼文顯示特殊訊息。"""
        content = render_report([], "2026-03-30", report_config)
        assert "今日無相關內容" in content

    def test_contains_star_scores(self, analyzed_posts, report_config):
        """報告包含星星評分。"""
        content = render_report(analyzed_posts, "2026-03-30", report_config)
        assert "⭐" in content


class TestSaveReport:
    """save_report 測試。"""

    def test_creates_file(self, report_config):
        """正確建立檔案。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_config["output"]["directory"] = tmpdir
            content = "# Test Report\nHello"
            path = save_report(content, report_config, "2026-03-30")

            assert os.path.exists(path)
            assert "threads_ai_trend_2026-03-30.md" in path

            with open(path, encoding="utf-8") as f:
                assert f.read() == content

    def test_creates_output_dir(self, report_config):
        """輸出目錄不存在時自動建立。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "sub", "dir")
            report_config["output"]["directory"] = nested
            path = save_report("test", report_config, "2026-03-30")
            assert os.path.exists(path)
