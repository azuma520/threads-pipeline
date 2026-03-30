"""analyzer 測試：prompt 組裝、JSON 解析、fallback。"""

import json
from unittest.mock import MagicMock, patch

import pytest

from threads_pipeline.analyzer import (
    _build_prompt,
    _fallback_analysis,
    _merge_analysis,
    _parse_analysis,
    analyze_posts,
)


class TestBuildPrompt:
    """_build_prompt 測試。"""

    def test_contains_all_post_ids(self, sample_posts):
        """prompt 包含所有貼文 ID。"""
        prompt = _build_prompt(sample_posts)
        for p in sample_posts:
            assert p["id"] in prompt

    def test_contains_usernames(self, sample_posts):
        """prompt 包含所有作者名稱。"""
        prompt = _build_prompt(sample_posts)
        for p in sample_posts:
            assert f"@{p['username']}" in prompt

    def test_contains_post_text(self, sample_posts):
        """prompt 包含貼文內容。"""
        prompt = _build_prompt(sample_posts)
        for p in sample_posts:
            assert p["text"] in prompt


class TestParseAnalysis:
    """_parse_analysis 測試。"""

    def test_valid_json(self, mock_claude_analysis_json):
        """正確 JSON 能解析。"""
        result = _parse_analysis(mock_claude_analysis_json)
        assert len(result) == 5
        assert all("id" in r for r in result)
        assert all("category" in r for r in result)
        assert all("score" in r for r in result)

    def test_json_with_code_block(self, mock_claude_analysis_json):
        """包在 markdown code block 裡的 JSON 也能解析。"""
        wrapped = f"```json\n{mock_claude_analysis_json}\n```"
        result = _parse_analysis(wrapped)
        assert len(result) == 5

    def test_malformed_json_returns_empty(self):
        """畸形 JSON 回傳空列表。"""
        result = _parse_analysis("this is not json at all")
        assert result == []

    def test_empty_string_returns_empty(self):
        """空字串回傳空列表。"""
        result = _parse_analysis("")
        assert result == []

    def test_score_values_in_range(self, mock_claude_analysis_json):
        """分數在 1-5 之間。"""
        result = _parse_analysis(mock_claude_analysis_json)
        for r in result:
            assert 1 <= r["score"] <= 5


class TestFallbackAnalysis:
    """_fallback_analysis 測試。"""

    def test_fallback_assigns_defaults(self, sample_posts):
        """fallback 給所有貼文預設值。"""
        result = _fallback_analysis(sample_posts)
        assert len(result) == len(sample_posts)
        for r in result:
            assert r["category"] == "觀點"
            assert r["score"] == 2
            assert "分析失敗" in r["summary"]


class TestMergeAnalysis:
    """_merge_analysis 測試。"""

    def test_merge_matches_by_id(self, sample_posts, mock_claude_analysis_json):
        """按 ID 正確合併。"""
        analysis = json.loads(mock_claude_analysis_json)
        merged = _merge_analysis(sample_posts, analysis)

        assert len(merged) == len(sample_posts)
        # 第一篇應該被標記為「產業動態」
        first = next(p for p in merged if p["id"] == "17841400000000001")
        assert first["category"] == "產業動態"
        assert first["score"] == 5

    def test_unmatched_posts_get_fallback(self, sample_posts):
        """分析結果缺少某些貼文時，給 fallback 值。"""
        partial_analysis = [
            {"id": "17841400000000001", "category": "新工具", "score": 4, "summary": "test"},
        ]
        merged = _merge_analysis(sample_posts, partial_analysis)

        matched = next(p for p in merged if p["id"] == "17841400000000001")
        assert matched["category"] == "新工具"

        unmatched = next(p for p in merged if p["id"] == "17841400000000002")
        assert unmatched["category"] == "觀點"
        assert unmatched["score"] == 2


class TestAnalyzePosts:
    """analyze_posts 整合測試。"""

    @patch("threads_pipeline.analyzer.anthropic.Anthropic")
    def test_normal_analysis(self, mock_anthropic_cls, sample_posts, mock_claude_analysis_json):
        """正常分析流程。"""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=mock_claude_analysis_json)]
        mock_client.messages.create.return_value = mock_response

        config = {"anthropic": {"model": "claude-sonnet-4-6", "max_tokens": 2048}}
        result = analyze_posts(sample_posts, config)

        assert len(result) == 5
        assert all("category" in p for p in result)
        assert all("score" in p for p in result)

    @patch("threads_pipeline.analyzer.anthropic.Anthropic")
    def test_api_error_uses_fallback(self, mock_anthropic_cls, sample_posts):
        """API 呼叫失敗時使用 fallback。"""
        mock_anthropic_cls.side_effect = Exception("API key invalid")

        config = {"anthropic": {"model": "claude-sonnet-4-6", "max_tokens": 2048}}
        result = analyze_posts(sample_posts, config)

        assert len(result) == 5
        assert all(p["category"] == "觀點" for p in result)
        assert all(p["score"] == 2 for p in result)

    def test_empty_posts(self):
        """空列表回傳空。"""
        config = {"anthropic": {"model": "claude-sonnet-4-6", "max_tokens": 2048}}
        result = analyze_posts([], config)
        assert result == []
