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


class TestParseSuggestionsJson:
    def test_valid(self):
        from threads_pipeline.planner import parse_suggestions_json
        stdout = '{"suggestions": [{"framework": 11, "name": "逆襲引流", "reason": "好"}]}'
        result = parse_suggestions_json(stdout)
        assert len(result) == 1
        assert result[0]["framework"] == 11
        assert result[0]["rank"] == 1

    def test_multiple_ranked(self):
        from threads_pipeline.planner import parse_suggestions_json
        stdout = '{"suggestions": [{"framework": 11, "name": "A", "reason": "r1"}, {"framework": 7, "name": "B", "reason": "r2"}]}'
        result = parse_suggestions_json(stdout)
        assert [s["rank"] for s in result] == [1, 2]

    def test_invalid_json_raises(self):
        from threads_pipeline.planner import parse_suggestions_json, PlannerError
        with pytest.raises(PlannerError, match="解析"):
            parse_suggestions_json("not json")

    def test_missing_suggestions_key_raises(self):
        from threads_pipeline.planner import parse_suggestions_json, PlannerError
        with pytest.raises(PlannerError):
            parse_suggestions_json('{"foo": []}')

    def test_missing_framework_field_raises(self):
        from threads_pipeline.planner import parse_suggestions_json, PlannerError
        with pytest.raises(PlannerError):
            parse_suggestions_json('{"suggestions": [{"name": "x"}]}')

    def test_strips_markdown_code_fence(self):
        from threads_pipeline.planner import parse_suggestions_json
        stdout = '```json\n{"suggestions": [{"framework": 11, "name": "A", "reason": "r"}]}\n```'
        result = parse_suggestions_json(stdout)
        assert result[0]["framework"] == 11


class TestPromptBuilders:
    def test_stage1_includes_full_frameworks_md(self):
        from threads_pipeline.planner import build_stage1_prompt
        fws_md = "## 結構總覽 ..."
        topic = "我的題目"
        prompt = build_stage1_prompt(topic=topic, frameworks_md=fws_md)
        assert fws_md in prompt
        assert topic in prompt
        assert "JSON" in prompt
        assert "suggestions" in prompt

    def test_stage2_includes_framework_and_style(self):
        from threads_pipeline.planner import build_stage2_prompt
        prompt = build_stage2_prompt(
            topic="題目",
            framework_section="編號：11\n名稱：逆襲引流",
            style_posts=[{"full_text": "貼文一", "engagement_rate": 3.5}],
            fmt="thread",
        )
        assert "題目" in prompt
        assert "逆襲引流" in prompt
        assert "貼文一" in prompt
        assert "thread" in prompt
        assert "3500" in prompt  # total length cap
        assert "目標受眾" in prompt  # required section

    def test_stage2_single_format(self):
        from threads_pipeline.planner import build_stage2_prompt
        prompt = build_stage2_prompt(
            topic="t", framework_section="fs", style_posts=[], fmt="single"
        )
        assert "single" in prompt
        assert "500 字" in prompt

    def test_stage2_no_style_posts_removes_section(self):
        """0 篇風格範本 → prompt 中完整移除「風格範本」段落，不留空標題。"""
        from threads_pipeline.planner import build_stage2_prompt
        prompt = build_stage2_prompt(
            topic="t", framework_section="fs", style_posts=[], fmt="thread"
        )
        assert "風格範本" not in prompt

    def test_stage2_with_style_posts_includes_section(self):
        from threads_pipeline.planner import build_stage2_prompt
        prompt = build_stage2_prompt(
            topic="t", framework_section="fs",
            style_posts=[{"full_text": "貼文A", "engagement_rate": 4.1}], fmt="thread"
        )
        assert "## 風格範本" in prompt
        assert "貼文A" in prompt


from unittest.mock import patch, MagicMock


class TestCallClaude:
    def test_success_prompt_in_argv(self):
        """prompt 透過 argv 傳入（對齊 analyzer.py），非 stdin。"""
        from threads_pipeline.planner import _call_claude
        with patch("threads_pipeline.planner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="result", stderr="")
            out = _call_claude("prompt text", model="haiku")
            assert out == "result"
            args, kwargs = mock_run.call_args
            cmd = args[0]
            assert cmd[0] == "claude"
            assert cmd[1] == "-p"
            assert cmd[2] == "prompt text"  # argv #2 = prompt
            assert "--model" in cmd
            assert "haiku" in cmd
            assert kwargs.get("input") is None  # NOT stdin
            assert kwargs["encoding"] == "utf-8"
            assert kwargs["timeout"] == 60

    def test_nonzero_exit_raises(self):
        from threads_pipeline.planner import _call_claude, PlannerError
        with patch("threads_pipeline.planner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="boom")
            with pytest.raises(PlannerError, match="claude"):
                _call_claude("p", model="haiku")

    def test_timeout_retries_once_then_raises(self):
        import subprocess
        from threads_pipeline.planner import _call_claude, PlannerError
        with patch("threads_pipeline.planner.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=60)
            with pytest.raises(PlannerError, match="超時"):
                _call_claude("p", model="haiku")
            assert mock_run.call_count == 2  # 1 次 + 1 次 retry

    def test_windows_uses_shell(self):
        from threads_pipeline.planner import _call_claude
        with patch("threads_pipeline.planner.platform.system", return_value="Windows"):
            with patch("threads_pipeline.planner.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
                _call_claude("p", model="haiku")
                _, kwargs = mock_run.call_args
                assert kwargs["shell"] is True

    def test_non_windows_no_shell(self):
        from threads_pipeline.planner import _call_claude
        with patch("threads_pipeline.planner.platform.system", return_value="Linux"):
            with patch("threads_pipeline.planner.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
                _call_claude("p", model="haiku")
                _, kwargs = mock_run.call_args
                assert kwargs["shell"] is False


class TestGeneratePlan:
    @pytest.fixture
    def frameworks_md(self):
        return (
            "## 結構總覽\n"
            "| # | 名稱 | 公式 | 適用場景 |\n"
            "|---|------|-----|---------|\n"
            "| 11 | 逆襲引流 | 積極結果 → 獲得感 | 分享成功經驗 |\n"
            "| 15 | 通用類 | 鉤子開頭 → 結尾 | 萬用結構 |\n"
        )

    def test_full_flow_with_framework_forced(self, frameworks_md):
        """給 --framework 時跳過 Stage 1，只呼叫 Stage 2。"""
        from threads_pipeline.planner import generate_plan
        with patch("threads_pipeline.planner._call_claude") as mock_call:
            mock_call.return_value = "# 題目\n- 框架：11 逆襲引流\n骨架內容"
            plan_md, framework_used = generate_plan(
                topic="題目",
                frameworks_md=frameworks_md,
                top_posts=[{"full_text": "貼文A", "engagement_rate": 3.0}],
                framework=11,
                fmt="thread",
                stage2_model="sonnet",
            )
            assert "骨架內容" in plan_md
            assert framework_used == 11
            assert mock_call.call_count == 1
            _, kwargs = mock_call.call_args
            assert kwargs["model"] == "sonnet"

    def test_full_flow_auto_picks_first_suggestion(self, frameworks_md):
        """無 framework 時 Stage 1 挑 + 用 auto 模式取第一個建議。"""
        from threads_pipeline.planner import generate_plan
        with patch("threads_pipeline.planner._call_claude") as mock_call:
            mock_call.side_effect = [
                '{"suggestions": [{"framework": 11, "name": "逆襲引流", "reason": "好"}]}',
                "# 題目\n骨架",
            ]
            plan_md, framework_used = generate_plan(
                topic="題目", frameworks_md=frameworks_md, top_posts=[],
                framework=None, fmt="thread", stage2_model="sonnet",
                auto=True,
            )
            assert framework_used == 11
            assert mock_call.call_count == 2

    def test_stage1_json_fail_raises(self, frameworks_md):
        from threads_pipeline.planner import generate_plan, PlannerError
        with patch("threads_pipeline.planner._call_claude") as mock_call:
            mock_call.return_value = "not json"
            with pytest.raises(PlannerError, match="JSON"):
                generate_plan(
                    topic="題目", frameworks_md=frameworks_md, top_posts=[],
                    framework=None, fmt="thread", stage2_model="sonnet", auto=True,
                )

    def test_unknown_framework_raises(self, frameworks_md):
        from threads_pipeline.planner import generate_plan, PlannerError
        with pytest.raises(PlannerError, match="框架"):
            generate_plan(
                topic="題目", frameworks_md=frameworks_md, top_posts=[],
                framework=99, fmt="thread", stage2_model="sonnet",
            )

    def test_suggest_only_returns_suggestions(self, frameworks_md):
        """`--suggest-only` 模式：只跑 Stage 1，回傳 suggestions list，不生 plan。"""
        from threads_pipeline.planner import suggest_frameworks
        with patch("threads_pipeline.planner._call_claude") as mock_call:
            mock_call.return_value = '{"suggestions": [{"framework": 11, "name": "逆襲引流", "reason": "好"}]}'
            out = suggest_frameworks(topic="題目", frameworks_md=frameworks_md)
            assert out[0]["framework"] == 11
            assert out[0]["rank"] == 1
            assert mock_call.call_count == 1

    def test_auto_hallucinated_framework_id_raises(self, frameworks_md):
        """LLM 回傳 frameworks_md 中不存在的 id 時，應 raise PlannerError 而非 TypeError。"""
        from threads_pipeline.planner import generate_plan, PlannerError
        with patch("threads_pipeline.planner._call_claude") as mock_call:
            mock_call.return_value = '{"suggestions": [{"framework": 999, "name": "幻想", "reason": "x"}]}'
            with pytest.raises(PlannerError, match="999|不存在"):
                generate_plan(
                    topic="題目", frameworks_md=frameworks_md, top_posts=[],
                    framework=None, fmt="thread", stage2_model="sonnet", auto=True,
                )
