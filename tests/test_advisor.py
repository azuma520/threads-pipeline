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


class TestCmdPlanNonInteractive:
    @pytest.fixture
    def fake_env(self, tmp_path, sample_db, monkeypatch):
        """Patch config loader, DB path, frameworks md, and drafts dir."""
        fake_fw_md = tmp_path / "frameworks.md"
        fake_fw_md.write_text(
            "## 結構總覽\n| # | 名稱 | 公式 | 適用場景 |\n|---|------|-----|---------|\n"
            "| 11 | 逆襲引流 | A → B | 分享成功經驗 |\n",
            encoding="utf-8",
        )
        drafts_dir = tmp_path / "drafts"
        drafts_dir.mkdir()

        monkeypatch.setattr(
            "threads_pipeline.advisor.load_config", lambda: {
                "storage": {"sqlite_path": str(sample_db)},
                "advisor": {"plan": {"stage2_model": "sonnet", "stage1_model": "haiku"}},
            },
            raising=False,
        )
        monkeypatch.setattr(
            "threads_pipeline.advisor.FRAMEWORKS_MD_PATH", str(fake_fw_md), raising=False,
        )
        monkeypatch.setattr(
            "threads_pipeline.advisor.DRAFTS_DIR", str(drafts_dir), raising=False,
        )
        return {"drafts": drafts_dir}

    def test_plan_with_framework_writes_file(self, fake_env):
        from threads_pipeline.advisor import _cmd_plan
        import argparse
        args = argparse.Namespace(
            topic="我學 Claude Code 一個月",
            topic_file=None, framework=11, auto=False, format=None, style_posts=None,
            model=None, suggest_only=False, json=False, overwrite=True, no_overwrite=False,
        )
        with patch("threads_pipeline.planner._call_claude", return_value="# 骨架內容"):
            rc = _cmd_plan(args)
        assert rc == 0
        files = list(fake_env["drafts"].glob("*.plan.md"))
        assert len(files) == 1
        assert "骨架內容" in files[0].read_text(encoding="utf-8")

    def test_plan_auto_uses_stage1_first_suggestion(self, fake_env):
        from threads_pipeline.advisor import _cmd_plan
        import argparse
        args = argparse.Namespace(
            topic="題目", topic_file=None, framework=None, auto=True, format=None,
            style_posts=None, model=None, suggest_only=False, json=False,
            overwrite=True, no_overwrite=False,
        )
        with patch("threads_pipeline.planner._call_claude") as mock_call:
            mock_call.side_effect = [
                '{"suggestions":[{"framework":11,"name":"逆襲引流","reason":"好"}]}',
                "# 骨架",
            ]
            rc = _cmd_plan(args)
        assert rc == 0

    def test_plan_suggest_only_json_goes_to_stdout(self, fake_env, capsys):
        from threads_pipeline.advisor import _cmd_plan
        import argparse, json as _json
        args = argparse.Namespace(
            topic="題目", topic_file=None, framework=None, auto=False, format=None,
            style_posts=None, model=None, suggest_only=True, json=True,
            overwrite=False, no_overwrite=False,
        )
        with patch("threads_pipeline.planner._call_claude",
                   return_value='{"suggestions":[{"framework":11,"name":"逆襲引流","reason":"好"}]}'):
            rc = _cmd_plan(args)
        assert rc == 0
        captured = capsys.readouterr()
        data = _json.loads(captured.out)
        assert data["suggestions"][0]["framework"] == 11

    def test_plan_json_parse_fail_exits_3(self, fake_env):
        from threads_pipeline.advisor import _cmd_plan
        import argparse
        args = argparse.Namespace(
            topic="題目", topic_file=None, framework=None, auto=True, format=None,
            style_posts=None, model=None, suggest_only=False, json=False,
            overwrite=True, no_overwrite=False,
        )
        with patch("threads_pipeline.planner._call_claude", return_value="not json"):
            rc = _cmd_plan(args)
        assert rc == 3

    def test_plan_unknown_framework_exits_1(self, fake_env):
        from threads_pipeline.advisor import _cmd_plan
        import argparse
        args = argparse.Namespace(
            topic="題目", topic_file=None, framework=99, auto=False, format=None,
            style_posts=None, model=None, suggest_only=False, json=False,
            overwrite=True, no_overwrite=False,
        )
        rc = _cmd_plan(args)
        assert rc == 1

    def test_plan_file_exists_no_overwrite_exits_4(self, fake_env):
        from threads_pipeline.advisor import _cmd_plan
        import argparse
        (fake_env["drafts"] / "題目.plan.md").write_text("existing", encoding="utf-8")
        args = argparse.Namespace(
            topic="題目", topic_file=None, framework=11, auto=False, format=None,
            style_posts=None, model=None, suggest_only=False, json=False,
            overwrite=False, no_overwrite=True,
        )
        with patch("threads_pipeline.planner._call_claude", return_value="new"):
            rc = _cmd_plan(args)
        assert rc == 4

    def test_plan_stdout_is_path_only_stderr_has_progress(self, fake_env, capsys):
        """agent-friendly：stdout 只含路徑、stderr 含進度訊息。"""
        from threads_pipeline.advisor import _cmd_plan
        import argparse
        args = argparse.Namespace(
            topic="題目", topic_file=None, framework=11, auto=False, format=None,
            style_posts=None, model=None, suggest_only=False, json=False,
            overwrite=True, no_overwrite=False,
        )
        with patch("threads_pipeline.planner._call_claude", return_value="# 骨架"):
            rc = _cmd_plan(args)
        captured = capsys.readouterr()
        assert rc == 0
        stdout_lines = [l for l in captured.out.strip().splitlines() if l.strip()]
        assert len(stdout_lines) == 1
        assert stdout_lines[0].endswith(".plan.md")
        assert "寫入" in captured.err or "框架" in captured.err

    def test_plan_non_tty_auto_fallback(self, fake_env, monkeypatch, capsys):
        """stdin 非 tty 且沒給 --auto / --framework → 自動等同 --auto，stderr 警告。"""
        from threads_pipeline.advisor import _cmd_plan
        import argparse
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)
        args = argparse.Namespace(
            topic="題目", topic_file=None, framework=None, auto=False, format=None,
            style_posts=None, model=None, suggest_only=False, json=False,
            overwrite=True, no_overwrite=False,
        )
        with patch("threads_pipeline.planner._call_claude") as mock_call:
            mock_call.side_effect = [
                '{"suggestions":[{"framework":11,"name":"逆襲引流","reason":"好"}]}',
                "# 骨架",
            ]
            rc = _cmd_plan(args)
        captured = capsys.readouterr()
        assert rc == 0
        assert "非 tty" in captured.err or "auto" in captured.err.lower()

    @pytest.mark.xfail(reason="Task 8b implements real q/cancel handling")
    def test_plan_interactive_q_exits_2(self, fake_env, monkeypatch):
        """使用者互動選 q → 整體 exit code 2。"""
        from threads_pipeline.advisor import _cmd_plan
        import argparse
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("builtins.input", lambda _: "q")
        args = argparse.Namespace(
            topic="題目", topic_file=None, framework=None, auto=False, format=None,
            style_posts=None, model=None, suggest_only=False, json=False,
            overwrite=True, no_overwrite=False,
        )
        with patch("threads_pipeline.planner._call_claude",
                   return_value='{"suggestions":[{"framework":11,"name":"A","reason":"r"}]}'):
            rc = _cmd_plan(args)
        assert rc == 2
