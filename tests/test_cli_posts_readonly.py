"""threads posts list / search 指令的 CliRunner 測試。"""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from threads_pipeline.threads_cli.cli import app

runner = CliRunner()


# === posts list ===

def test_posts_list_human_mode():
    """人類模式：stdout 含每則 post 的 id + text 片段。"""
    with patch("threads_pipeline.threads_cli.posts.list_my_posts",
               return_value={"posts": [
                   {"id": "P1", "text": "hello world", "timestamp": "2026-04-17T00:00:00Z"},
                   {"id": "P2", "text": "second post", "timestamp": "2026-04-16T00:00:00Z"},
               ], "next_cursor": None}), \
         patch("threads_pipeline.threads_cli.posts.require_token", return_value="fake"):
        result = runner.invoke(app, ["posts", "list"])
    assert result.exit_code == 0
    assert "P1" in result.output
    assert "hello world" in result.output
    assert "P2" in result.output


def test_posts_list_json_mode():
    """JSON 模式：envelope 含 posts + （無下一頁時）不含 next_cursor。"""
    fake = {"posts": [{"id": "P1"}], "next_cursor": None}
    with patch("threads_pipeline.threads_cli.posts.list_my_posts", return_value=fake), \
         patch("threads_pipeline.threads_cli.posts.require_token", return_value="fake"):
        result = runner.invoke(app, ["posts", "list", "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["ok"] is True
    assert parsed["data"]["posts"] == [{"id": "P1"}]
    assert "next_cursor" not in parsed  # None 不進 envelope


def test_posts_list_has_next_cursor_json_mode():
    """有下一頁時 JSON envelope 含 next_cursor。"""
    fake = {"posts": [{"id": "P1"}], "next_cursor": "CURSOR_X"}
    with patch("threads_pipeline.threads_cli.posts.list_my_posts", return_value=fake), \
         patch("threads_pipeline.threads_cli.posts.require_token", return_value="fake"):
        result = runner.invoke(app, ["posts", "list", "--json"])
    parsed = json.loads(result.output)
    assert parsed["next_cursor"] == "CURSOR_X"


def test_posts_list_has_next_cursor_human_mode():
    """有下一頁時 stderr 提示下一頁 cursor（人類模式）。"""
    fake = {"posts": [{"id": "P1"}], "next_cursor": "CURSOR_X"}
    with patch("threads_pipeline.threads_cli.posts.list_my_posts", return_value=fake), \
         patch("threads_pipeline.threads_cli.posts.require_token", return_value="fake"):
        result = runner.invoke(app, ["posts", "list"])
    # Typer CliRunner 預設 stderr 混入 result.output；改用 mix_stderr=False 才能拆，
    # 但此處斷言 combined 有 "--cursor" 即可
    assert "--cursor" in result.output
    assert "CURSOR_X" in result.output


def test_posts_list_passes_cursor():
    """--cursor 旗標應以 keyword 傳到 list_my_posts。

    Task 6 Step 3 handler 寫 `list_my_posts(token, limit=..., cursor=...)`，
    所以 assert kwargs["cursor"]；若未來有人改回 positional 會立刻 fail。
    """
    with patch("threads_pipeline.threads_cli.posts.list_my_posts",
               return_value={"posts": [], "next_cursor": None}) as mock_list, \
         patch("threads_pipeline.threads_cli.posts.require_token", return_value="fake"):
        runner.invoke(app, ["posts", "list", "--cursor", "PREV_CURSOR"])
    assert mock_list.call_args.kwargs["cursor"] == "PREV_CURSOR"


def test_posts_list_limit_clamp_warning_json():
    """--limit 超過 100 應 clamp：envelope 含 warning + stderr 同步印 [WARN]。

    Spec §3「警告通道規則」：warnings 同時走 stderr（人類可讀）與 envelope
    （Agent 可讀）。CliRunner 預設 mix_stderr=True，stderr 會合併進 result.output。
    """
    with patch("threads_pipeline.threads_cli.posts.list_my_posts",
               return_value={"posts": [], "next_cursor": None}) as mock_list, \
         patch("threads_pipeline.threads_cli.posts.require_token", return_value="fake"):
        result = runner.invoke(app, ["posts", "list", "--limit", "500", "--json"])
    assert result.exit_code == 0
    # 1) stderr 同步：result.output 含 [WARN] 前綴（mix_stderr 合併模式）
    assert "[WARN]" in result.output
    assert "LIMIT_CLAMPED" in result.output or "clamp" in result.output.lower()
    # 2) envelope 含 warning——CliRunner 合併後 stdout / stderr 順序不保證
    #    （實測 JSON 先、[WARN] 後），故用 `{` ... `}` 配對切出 JSON 片段再 parse
    json_start = result.output.find("{")
    json_end = result.output.rfind("}")
    assert json_start >= 0 and json_end > json_start, (
        f"no JSON envelope found in output: {result.output!r}"
    )
    parsed = json.loads(result.output[json_start:json_end + 1])
    assert any(w["code"] == "LIMIT_CLAMPED" for w in parsed.get("warnings", []))
    # 3) 傳給 core 的 limit 應被 clamp 到 100
    assert mock_list.call_args.kwargs["limit"] == 100


# === posts search ===

def test_posts_search_english_human_mode():
    """英文關鍵字：正常流程，不觸發 CJK warning。"""
    fake_posts = [{"id": "P1", "text": "hello AI"}]
    with patch("threads_pipeline.threads_cli.posts._search_keyword",
               return_value=fake_posts), \
         patch("threads_pipeline.threads_cli.posts.require_token", return_value="fake"):
        result = runner.invoke(app, ["posts", "search", "AI"])
    assert result.exit_code == 0
    assert "P1" in result.output
    assert "EMPTY_RESULT_CJK" not in result.output


def test_posts_search_cjk_empty_json_mode():
    """中文關鍵字 + 0 筆結果 → warnings 含 EMPTY_RESULT_CJK。"""
    with patch("threads_pipeline.threads_cli.posts._search_keyword",
               return_value=[]), \
         patch("threads_pipeline.threads_cli.posts.require_token", return_value="fake"):
        result = runner.invoke(app, ["posts", "search", "人工智慧", "--json"])
    assert result.exit_code == 0
    json_start = result.output.find("{")
    json_end = result.output.rfind("}")
    assert json_start >= 0 and json_end > json_start
    parsed = json.loads(result.output[json_start:json_end + 1])
    warning_codes = [w["code"] for w in parsed.get("warnings", [])]
    assert "EMPTY_RESULT_CJK" in warning_codes


def test_posts_search_cjk_nonempty_no_warning():
    """中文關鍵字但有結果 → 不加 EMPTY_RESULT_CJK warning（只有空才加）。"""
    with patch("threads_pipeline.threads_cli.posts._search_keyword",
               return_value=[{"id": "P1", "text": "中文 post"}]), \
         patch("threads_pipeline.threads_cli.posts.require_token", return_value="fake"):
        result = runner.invoke(app, ["posts", "search", "中文", "--json"])
    json_start = result.output.find("{")
    json_end = result.output.rfind("}")
    assert json_start >= 0 and json_end > json_start
    parsed = json.loads(result.output[json_start:json_end + 1])
    warning_codes = [w["code"] for w in parsed.get("warnings", [])]
    assert "EMPTY_RESULT_CJK" not in warning_codes


def test_posts_search_zero_result_exit_0():
    """結果 0 筆不是 error（exit 0）。"""
    with patch("threads_pipeline.threads_cli.posts._search_keyword",
               return_value=[]), \
         patch("threads_pipeline.threads_cli.posts.require_token", return_value="fake"):
        result = runner.invoke(app, ["posts", "search", "xyz_no_match"])
    assert result.exit_code == 0
