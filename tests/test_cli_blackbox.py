"""Subprocess 黑箱測試——跨越 argparse/Typer 邊界的 regression 防線。

這些測試從 shell 真跑 `threads` CLI（透過 python -m），斷言：
- exit code
- stdout/stderr 中我方可控的輸出（[DRY RUN] / [OK] / [ERROR] / [WARN] 前綴 + payload 片段）

**不**斷言框架（argparse/Click）自動生成的 error 訊息逐字。
"""

import os
import subprocess
import sys


def run_threads(args: list[str], env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """跑 `python -m threads_pipeline.threads_cli.cli ...`，捕捉 stdout/stderr。"""
    env = os.environ.copy()
    # 設假 token，讓 require_token() 不先擋；真實 API 不會被呼叫（flag 組合在那之前就擋）
    env.setdefault("THREADS_ACCESS_TOKEN", "test_fake_token_not_real")
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-m", "threads_pipeline.threads_cli.cli", *args],
        capture_output=True,
        text=True,
        env=env,
        encoding="utf-8",
    )


# === Group 1: 基本 help / version ===

def test_bbox_version():
    """threads --version → exit 0, 含版本號。"""
    r = run_threads(["--version"])
    assert r.returncode == 0
    assert "0.1.0" in r.stdout


def test_bbox_help():
    """threads --help → exit 0, 含 post / posts 字樣。"""
    r = run_threads(["--help"])
    assert r.returncode == 0
    assert "post" in r.stdout.lower()


def test_bbox_no_subcommand_prints_help():
    """threads（無 subcommand）→ exit 0 或 2（argparse 印 help 是 0；Typer 可能是 2），
    關鍵是 stdout/stderr 任一含 usage/help 訊息。"""
    r = run_threads([])
    # argparse: 我們 main() 有 parser.print_help() return 0
    # Typer: 預設也印 help，但 exit code 可能 0 或 2（視實作）
    assert r.returncode in (0, 2)
    combined = r.stdout + r.stderr
    assert "post" in combined.lower()


def test_bbox_unknown_subcommand_exits_2():
    """threads wrong → exit 2（argparse / Click 都是 2）。"""
    r = run_threads(["wrong_subcommand"])
    assert r.returncode == 2


# === Group 2: publish flag 組合 ===

def test_bbox_publish_dry_run_output():
    """threads post publish "text"（無 --confirm）→ dry-run，exit 0，stdout 含 [DRY RUN]。"""
    r = run_threads(["post", "publish", "hello world"])
    assert r.returncode == 0
    assert "[DRY RUN]" in r.stdout
    assert "hello world" in r.stdout


def test_bbox_publish_yes_without_confirm_exits_2():
    """threads post publish "x" --yes（無 --confirm）→ exit 2（flag 組合錯誤）。"""
    r = run_threads(["post", "publish", "x", "--yes"])
    assert r.returncode == 2
    # 我方輸出：stderr 含 [ERROR] 前綴
    assert "[ERROR]" in r.stderr


def test_bbox_publish_confirm_without_yes_in_ci_does_not_publish():
    """--confirm 沒有 --yes，在 subprocess（無真實使用者輸入）下，必須不真的發文。

    兩種可接受行為：
    - POSIX：`sys.stdin.isatty()` 回 False → validate_confirm_yes 擋下 → exit 2 + stderr [ERROR]
    - Windows：subprocess 的 stdin 仍被視為 TTY（平台行為），但 interactive_confirm
      讀 input() 時拿到 EOFError → 視為取消 → exit 0 + 印 "(cancelled)"

    共同不變式：**不會看到 [OK] Published**（沒有真的發文）。
    """
    r = run_threads(["post", "publish", "hello", "--confirm"])
    combined = r.stdout + r.stderr
    # 絕不能真發文
    assert "[OK] Published" not in combined
    # 要嘛是 validate_confirm_yes 擋下（exit 2 + [ERROR]），要嘛是 interactive 被取消（exit 0 + cancelled）
    if r.returncode == 2:
        assert "[ERROR]" in r.stderr
    else:
        assert r.returncode == 0
        assert "cancelled" in combined.lower()


def test_bbox_publish_missing_text_exits_2():
    """threads post publish（缺 text）→ exit 2（框架層，只驗 exit code）。"""
    r = run_threads(["post", "publish"])
    assert r.returncode == 2


# === Group 3: reply flag 組合 ===

def test_bbox_reply_dry_run_output():
    """threads reply POST_123 "text"（無 --confirm）→ dry-run，exit 0，stdout 含 [DRY RUN]。"""
    r = run_threads(["reply", "POST_123", "my reply"])
    assert r.returncode == 0
    assert "[DRY RUN]" in r.stdout
    assert "POST_123" in r.stdout


def test_bbox_reply_yes_without_confirm_exits_2():
    """threads reply POST_123 "x" --yes（無 --confirm）→ exit 2。"""
    r = run_threads(["reply", "POST_123", "x", "--yes"])
    assert r.returncode == 2
    assert "[ERROR]" in r.stderr


def test_bbox_reply_missing_text_exits_2():
    """threads reply POST_123（缺 text）→ exit 2。"""
    r = run_threads(["reply", "POST_123"])
    assert r.returncode == 2


# === Group 4: publish-chain flag 組合 ===

def test_bbox_publish_chain_dry_run_output(tmp_path):
    """threads post publish-chain FILE（無 --confirm）→ dry-run，exit 0，stdout 含 [DRY RUN]。"""
    chain_file = tmp_path / "chain.txt"
    chain_file.write_text("第一則\n第二則\n", encoding="utf-8")
    r = run_threads(["post", "publish-chain", str(chain_file)])
    assert r.returncode == 0
    assert "[DRY RUN]" in r.stdout
    assert "2 posts" in r.stdout


def test_bbox_publish_chain_nonexistent_file_exits_1():
    """threads post publish-chain nonexistent.txt → exit 1（OSError）。"""
    r = run_threads(["post", "publish-chain", "/nonexistent/path/xyz.txt"])
    assert r.returncode == 1
    assert "[ERROR]" in r.stderr


def test_bbox_publish_chain_retry_policy_exits_2(tmp_path):
    """--on-failure retry（Level 1 未實作）→ exit 2（NotImplementedError）。"""
    chain_file = tmp_path / "chain.txt"
    chain_file.write_text("a\n", encoding="utf-8")
    r = run_threads([
        "post", "publish-chain", str(chain_file),
        "--confirm", "--yes", "--on-failure", "retry"
    ])
    assert r.returncode == 2


# === Group 5: 全域 flag ===

def test_bbox_json_flag_accepted():
    """--json 旗標應可被接受（batch A inert、batch B 會實作）→ 不 exit 2。"""
    r = run_threads(["--json", "post", "publish", "hello"])
    # 不管是 dry-run（0）還是其他合法 exit code，不應該是 unknown flag 的 2
    assert r.returncode == 0
    assert "hello" in r.stdout


# === Group 6: B2 account info ===

def test_bbox_account_info_help_exits_0():
    """threads account info --help → exit 0, 含 info 關鍵字。"""
    r = run_threads(["account", "info", "--help"])
    assert r.returncode == 0
    # Click 會印 "Usage:"
    assert "info" in r.stdout.lower()


def test_bbox_account_insights_help_exits_0():
    r = run_threads(["account", "insights", "--help"])
    assert r.returncode == 0
    assert "insights" in r.stdout.lower()


# === Group 7: B2 posts list ===

def test_bbox_posts_list_help_exits_0():
    r = run_threads(["posts", "list", "--help"])
    assert r.returncode == 0
    combined = r.stdout + r.stderr
    assert "--cursor" in combined
    assert "--limit" in combined


# === Group 8: B2 post insights ===

def test_bbox_post_insights_help_exits_0():
    r = run_threads(["post", "insights", "--help"])
    assert r.returncode == 0
    combined = r.stdout + r.stderr
    assert "POST_ID" in combined.upper() or "post_id" in combined


# === Group 9: B2 posts search ===

def test_bbox_posts_search_help_shows_standard_access_warning():
    """posts search --help 應在文案中提到 Standard Access 限制。"""
    r = run_threads(["posts", "search", "--help"])
    assert r.returncode == 0
    combined = r.stdout + r.stderr
    assert "Standard Access" in combined or "standard access" in combined.lower()


def test_bbox_posts_search_missing_keyword_exits_2():
    """threads posts search（缺 keyword）→ exit 2。"""
    r = run_threads(["posts", "search"])
    assert r.returncode == 2


# === Group 10: B2 post replies ===

def test_bbox_post_replies_help_exits_0():
    r = run_threads(["post", "replies", "--help"])
    assert r.returncode == 0
    combined = r.stdout + r.stderr
    assert "--cursor" in combined


def test_bbox_post_replies_missing_post_id_exits_2():
    """threads post replies（缺 post_id）→ exit 2（Typer 框架層）。"""
    r = run_threads(["post", "replies"])
    assert r.returncode == 2


def test_bbox_post_insights_missing_post_id_exits_2():
    """threads post insights（缺 post_id）→ exit 2。"""
    r = run_threads(["post", "insights"])
    assert r.returncode == 2
