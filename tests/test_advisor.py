"""advisor 測試。"""

import json
import sqlite3
import pytest
from threads_pipeline.advisor import generate_analysis, generate_analysis_json


@pytest.fixture
def sample_db(tmp_path):
    """建立含範例數據的測試 DB。"""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE post_insights (
            collected_date TEXT NOT NULL, post_id TEXT NOT NULL,
            text_preview TEXT, full_text TEXT, posted_at TEXT,
            post_hour_local INTEGER, username TEXT,
            views INTEGER DEFAULT 0, likes INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0, reposts INTEGER DEFAULT 0,
            quotes INTEGER DEFAULT 0, author_reply_count INTEGER DEFAULT 0,
            PRIMARY KEY (collected_date, post_id)
        );
        CREATE TABLE account_insights (
            collected_date TEXT NOT NULL PRIMARY KEY,
            followers INTEGER DEFAULT 0, total_views INTEGER DEFAULT 0,
            total_likes INTEGER DEFAULT 0, total_replies INTEGER DEFAULT 0,
            total_reposts INTEGER DEFAULT 0
        );
        INSERT INTO post_insights VALUES
            ('2026-04-01', 'p1', '高表現AI文', '我是那種很依賴AI學習的人，尤其喜歡拿YouTube影片當素材', '2026-03-06T18:06:00+0000', 18, 'azuma01130626', 61485, 1200, 300, 200, 100, 12),
            ('2026-04-01', 'p2', '低表現教學文', '教學：如何設定環境變數，這是一個基礎的開發技巧', '2026-03-07T11:00:00+0000', 11, 'azuma01130626', 500, 10, 2, 1, 0, 0),
            ('2026-04-01', 'p3', '中等觀點文', '不知道大家有沒有試過，叫AI寫下它對你的觀察', '2026-03-08T19:28:00+0000', 19, 'azuma01130626', 353, 8, 4, 2, 1, 3);
        INSERT INTO account_insights VALUES
            ('2026-03-25', 200, 4000, 80, 40, 15),
            ('2026-04-01', 206, 5796, 110, 55, 22);
    """)
    conn.commit()
    conn.close()
    return db_path


class TestGenerateAnalysis:
    def test_normal_mode(self, sample_db):
        conn = sqlite3.connect(str(sample_db))
        report = generate_analysis(conn, "2026-04-02")
        conn.close()
        assert "帳號現況" in report
        assert "206" in report
        assert "Top" in report

    def test_empty_db(self, tmp_path):
        db_path = tmp_path / "empty.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript("""
            CREATE TABLE post_insights (
                collected_date TEXT NOT NULL, post_id TEXT NOT NULL,
                text_preview TEXT, full_text TEXT, posted_at TEXT,
                post_hour_local INTEGER, username TEXT,
                views INTEGER DEFAULT 0, likes INTEGER DEFAULT 0,
                replies INTEGER DEFAULT 0, reposts INTEGER DEFAULT 0,
                quotes INTEGER DEFAULT 0, author_reply_count INTEGER DEFAULT 0,
                PRIMARY KEY (collected_date, post_id)
            );
            CREATE TABLE account_insights (
                collected_date TEXT NOT NULL PRIMARY KEY,
                followers INTEGER DEFAULT 0, total_views INTEGER DEFAULT 0,
                total_likes INTEGER DEFAULT 0, total_replies INTEGER DEFAULT 0,
                total_reposts INTEGER DEFAULT 0
            );
        """)
        conn.commit()
        report = generate_analysis(conn, "2026-04-02")
        conn.close()
        assert "請先執行 Pipeline" in report


class TestGenerateAnalysisJson:
    def test_outputs_valid_json(self, sample_db):
        conn = sqlite3.connect(str(sample_db))
        result = generate_analysis_json(conn)
        conn.close()
        assert isinstance(result, dict)
        assert "followers" in result
        assert "avg_engagement_rate" in result
        assert "top_post_hours" in result


from unittest.mock import patch, MagicMock
from threads_pipeline.advisor import review_draft, _build_review_prompt


class TestBuildReviewPrompt:
    def test_includes_draft(self):
        prompt = _build_review_prompt(
            draft="這是我的草稿",
            analysis_json={"followers": 206},
            plan_content=None,
        )
        assert "這是我的草稿" in prompt
        assert "206" in prompt

    def test_includes_plan_when_provided(self):
        prompt = _build_review_prompt(
            draft="草稿",
            analysis_json={},
            plan_content="## 目標受眾\n- 誰：AI 初學者",
        )
        assert "AI 初學者" in prompt

    def test_prompt_length_under_limit(self):
        prompt = _build_review_prompt(
            draft="短草稿",
            analysis_json={"followers": 206},
            plan_content="短 plan",
        )
        assert len(prompt) < 8000


class TestReviewDraft:
    @patch("threads_pipeline.advisor.subprocess.run")
    def test_successful_review(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="整體評分：⭐⭐⭐⭐ (4/5)\n\n✅ 鉤子 — 好",
        )
        result = review_draft("這是草稿", analysis_json={"followers": 206})
        assert "4/5" in result
        assert mock_run.called

    @patch("threads_pipeline.advisor.subprocess.run")
    def test_failed_review(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        result = review_draft("草稿", analysis_json={})
        assert "審查失敗" in result


def test_review_prompt_plan_truncation_is_4000():
    long_plan = "P" * 5000
    prompt = _build_review_prompt(draft="draft", analysis_json={}, plan_content=long_plan)
    assert "P" * 4000 in prompt
    assert "P" * 4001 not in prompt
