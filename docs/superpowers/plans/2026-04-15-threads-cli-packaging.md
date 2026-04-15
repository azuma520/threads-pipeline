# Threads CLI Packaging Implementation Plan (v1.1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `threads_pipeline` 打包成 pip-installable CLI 工具。新增 `threads-advisor`、`threads`、`cli-anything-threads` 三個指令，讓使用者 / Agent 能以短指令呼叫既有功能（`advisor plan/review/analyze`）並新增 Threads API 操作（`post publish`、`reply`、`post publish-chain`）。

**Architecture:** 扁平 Python package layout（既有 .py 檔都在 repo root），新增 `publisher.py` 模組（repo root，發文邏輯）+ `threads_cli/` 子套件（repo root 下的資料夾；argparse dispatch table + JSON/人讀輸出 + safety + SKILL.md）。pyproject.toml 用 `package-dir` + 明確 `packages` list 把扁平目錄映射成 `threads_pipeline` + `threads_pipeline.threads_cli` 兩層。寫入指令四層安全：Token 檢查 + 預設 dry-run + 互動確認 + `--yes` Agent 模式。

**Tech Stack:** Python 3.13、setuptools（pyproject.toml）、argparse（保留現有）、requests、pytest、mock。

**Spec:** `docs/superpowers/specs/2026-04-15-threads-cli-packaging-design.md`（v1.1 審查後版）

**Plan 修訂歷程：**
- v1.0：初版（12 task）
- v1.1（本版）：雙審查後修訂 — 修 pyproject packages 配置、檔案路徑誤導、Windows UTF-8 stdout reconfigure、argparse defensive getattr、publish_chain opener-fail 語義、`_post()` 防禦性 error 解析、Token scope 前置、smoke test reply 合併、測試 boundary / 精確度

**執行範圍：批次 A**。批次 B（list / insights / replies / account / delete）另起 plan。

---

## 關鍵概念：扁平 layout 與路徑對應

本專案是**扁平 layout**：repo root `桌面/threads_pipeline/` 就是 Python package `threads_pipeline` 本身。`advisor.py`、`threads_client.py` 等都在 repo root 直接放。

Plan 中所有檔案路徑以**repo root 為基準**寫成 `./x.py` 格式，對應的 Python import 路徑是 `threads_pipeline.x`。

| 檔案系統路徑（建檔位置） | Python import 路徑 |
|---|---|
| `./advisor.py` | `threads_pipeline.advisor` |
| `./publisher.py`（新增） | `threads_pipeline.publisher` |
| `./threads_cli/__init__.py`（新增） | `threads_pipeline.threads_cli` |
| `./threads_cli/cli.py`（新增） | `threads_pipeline.threads_cli.cli` |
| `./threads_cli/publisher.py` | ❌ 不要建這個！publisher 不在 threads_cli 裡 |

**錯誤示範**（v1.0 plan 曾寫的誤導路徑）：
- ❌ `threads_pipeline/publisher.py`（repo 內沒有 `threads_pipeline/` 子資料夾）
- ❌ `threads_pipeline/threads_cli/`（同上）

**正確建檔位置**：
- ✅ `./publisher.py`（跟 `advisor.py` 同層）
- ✅ `./threads_cli/`（跟 `scripts/` 同層）

---

## File Structure

### 新增檔案（repo root 相對路徑）

- `./pyproject.toml` — 打包設定、三個 entry points
- `./publisher.py` — 發文邏輯（publish_text / reply_to / publish_chain）
- `./threads_cli/__init__.py` — package marker
- `./threads_cli/cli.py` — argparse + dispatch table
- `./threads_cli/output.py` — JSON / 人讀格式化
- `./threads_cli/safety.py` — Token / confirm / yes 驗證
- `./threads_cli/SKILL.md` — Agent 使用說明
- `./tests/test_publisher.py` — publisher 單元測試
- `./tests/test_threads_cli.py` — CLI 單元測試
- `./tests/test_cli_safety.py` — safety 層測試
- `./drafts/smoke-test.txt` — 手動 smoke 用串文檔案

### 修改檔案

- `./CLAUDE.md` — Commands 區塊補新指令（雙軌並列）

### 不動

- `./advisor.py` / `./analyzer.py` / `./threads_client.py` / `./main.py` / `./insights_tracker.py` / `./db_helpers.py` / `./report.py`
- `./scripts/demo_publish_reply.py` — 暫留當 reference

---

## Task 0: pyproject.toml + 基礎打包驗證

建立打包設定，驗證 `pip install -e .` 能正確安裝。**Level 1 地基，不通過不往下**。

**Files:**
- Create: `./pyproject.toml`

- [ ] **Step 1: 建立 pyproject.toml**

寫檔案 `./pyproject.toml`（repo root）：

```toml
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "threads-pipeline"
version = "0.1.0"
description = "Threads API operations & post advisor (CLI-Anything compatible)"
requires-python = ">=3.13"
readme = "README.md"
license = {text = "MIT"}
authors = [{name = "azuma520"}]
keywords = ["threads", "meta", "cli", "agent", "social-media"]

dependencies = [
    "requests>=2.31",
    "pyyaml>=6.0",
    "jinja2>=3.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
]

[project.scripts]
threads-advisor      = "threads_pipeline.advisor:main"
threads              = "threads_pipeline.threads_cli.cli:main"
cli-anything-threads = "threads_pipeline.threads_cli.cli:main"

[project.urls]
Homepage   = "https://github.com/azuma520/threads_pipeline"
Repository = "https://github.com/azuma520/threads_pipeline"
Issues     = "https://github.com/azuma520/threads_pipeline/issues"

# ─────────────────────────────────────────────────
# 扁平 layout 的 package 設定
# 明示 packages list，不用 find（避免把 tests/ scripts/ 等誤當 package）
# ─────────────────────────────────────────────────
[tool.setuptools]
package-dir = {"threads_pipeline" = ".", "threads_pipeline.threads_cli" = "threads_cli"}
packages = ["threads_pipeline", "threads_pipeline.threads_cli"]

[tool.setuptools.package-data]
"threads_pipeline" = ["templates/*.j2", "references/*.md"]
"threads_pipeline.threads_cli" = ["SKILL.md"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

**關鍵差異 vs v1.0**：
- 用**明示 `packages` list** 取代 `packages.find`（避免 `tests/` 等誤被當 package）
- `package-dir` 同時映射 `threads_pipeline = "."` 和 `threads_pipeline.threads_cli = "threads_cli"`，兩層都要寫

- [ ] **Step 2: 驗證 pip install -e . 成功**

Run: `pip install -e ".[dev]"`
Expected: 看到 `Successfully installed threads-pipeline-0.1.0`，無 error。

若 error「Multiple top-level packages discovered」或「No module named threads_pipeline」→ package-dir / packages 配置錯，停下檢查。

**注意**：此時 `threads_cli/` 資料夾還不存在，editable install 會抱怨但不 fail（entry_point 驗證 lazy），這是預期的。**不要在此時呼叫 `threads --version`** — Task 1 前它會 ModuleNotFoundError。

- [ ] **Step 3: 驗證 threads-advisor 指令已建立**

Run: `where threads-advisor`（Windows）或 `which threads-advisor`（Unix）
Expected: 印出 `.exe` 路徑（Windows 在 `Python313\Scripts\`）。

- [ ] **Step 4: 驗證 threads-advisor 能真的執行**

Run: `threads-advisor list-frameworks`
Expected: 印出 16+1 框架清單，與 `python -m threads_pipeline.advisor list-frameworks` 輸出相同。

- [ ] **Step 5: 既有測試回歸檢查**

Run: `pytest`
Expected: 全通過。

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml
git commit -m "feat(packaging): 加 pyproject.toml，threads-advisor 指令可用

- 扁平 layout 用 package-dir + 明示 packages list 配置
- package-dir 同時映射 threads_pipeline = \".\" 和 threads_pipeline.threads_cli = \"threads_cli\"
- 三個 entry points 註冊（threads-advisor、threads、cli-anything-threads）
- threads / cli-anything-threads 指向 threads_cli.cli:main（尚未建檔，下一 task 補）

驗證：
- pip install -e \".[dev]\" 成功
- threads-advisor list-frameworks 輸出與 python -m 相同
- 既有 pytest 全通過"
```

---

## Task 1: threads_cli 骨架 + dispatch table

建立 CLI 模組的最小可執行版本。`threads` 指令能 `--help` 和 `--version`，子命令都回 NotImplementedError stub。

**Files:**
- Create: `./threads_cli/__init__.py`
- Create: `./threads_cli/cli.py`
- Create: `./threads_cli/output.py`
- Create: `./tests/test_threads_cli.py`

- [ ] **Step 1: 寫 __init__.py**

檔案 `./threads_cli/__init__.py`：

```python
"""Threads CLI — 對 Threads API 的 CLI 包裝。"""

__version__ = "0.1.0"
```

- [ ] **Step 2: 寫 output.py（格式化 + 錯誤處理）**

檔案 `./threads_cli/output.py`：

```python
"""CLI 輸出格式化（JSON / 人讀）。"""

import json
import sys
from typing import Any


def emit(data: Any, *, json_mode: bool = False, message: str | None = None) -> None:
    """印出資料；JSON 模式印合法 JSON，否則人讀。"""
    if json_mode:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    if message:
        print(message)
    if isinstance(data, dict):
        for k, v in data.items():
            print(f"  {k}: {v}")
    elif isinstance(data, list):
        for item in data:
            print(f"  - {item}")
    else:
        print(data)


def error(message: str, *, exit_code: int = 1) -> None:
    """印 error 到 stderr 並 exit（raises SystemExit）。

    Callers 不需要加 return — 此函式一定 exit。
    """
    print(f"[ERROR] {message}", file=sys.stderr)
    sys.exit(exit_code)


def warn(message: str) -> None:
    """印 warning 到 stderr（不 exit）。"""
    print(f"[WARN] {message}", file=sys.stderr)
```

**關鍵差異 vs v1.0**：
- 用 `[ERROR]` / `[WARN]` 取代 `✗` / `⚠` — Windows cp950 安全
- error() 的 docstring 明示「一定 exit」，後續不要寫 dead code `return 1`

- [ ] **Step 3: 寫 failing test**

檔案 `./tests/test_threads_cli.py`：

```python
"""CLI 層單元測試。"""

import subprocess
import sys
from unittest.mock import patch

import pytest


def test_threads_cli_version():
    """threads --version 應印出版本號。"""
    result = subprocess.run(
        [sys.executable, "-m", "threads_pipeline.threads_cli.cli", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "0.1.0" in result.stdout


def test_threads_cli_help():
    """threads --help 應印使用說明且 exit 0。"""
    result = subprocess.run(
        [sys.executable, "-m", "threads_pipeline.threads_cli.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "posts" in result.stdout or "post" in result.stdout
```

- [ ] **Step 4: Run — expect fail**

Run: `pytest tests/test_threads_cli.py -v`
Expected: FAIL — `No module named threads_pipeline.threads_cli.cli`

- [ ] **Step 5: 寫 cli.py（骨架 + dispatch table + UTF-8 reconfigure）**

檔案 `./threads_cli/cli.py`：

```python
"""Threads CLI 入口 — argparse + dispatch table。"""

import argparse
import sys

# Windows UTF-8：reconfigure 在 Python 啟動後才有效，setdefault("PYTHONUTF8", "1") 無用
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from threads_pipeline.threads_cli import __version__
from threads_pipeline.threads_cli.output import emit, error, warn


def _build_parser() -> argparse.ArgumentParser:
    """建立 argparse parser 樹。"""
    parser = argparse.ArgumentParser(
        prog="threads",
        description="Threads API operations CLI (CLI-Anything compatible)",
    )
    parser.add_argument(
        "--version", action="version", version=f"threads {__version__}"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output as JSON (batch A: parsed but inert)"
    )

    subparsers = parser.add_subparsers(dest="resource", required=False)

    # posts (複數：列表操作) — 批次 B
    posts = subparsers.add_parser("posts", help="Posts list operations (batch B)")
    posts_sub = posts.add_subparsers(dest="action", required=True)

    posts_search = posts_sub.add_parser("search", help="Search posts by keyword")
    posts_search.add_argument("keyword", help="Search keyword")
    posts_search.add_argument("--limit", type=int, default=25, help="Max results (capped at 25)")

    # post (單數：單項操作)
    post = subparsers.add_parser("post", help="Single post operations")
    post_sub = post.add_subparsers(dest="action", required=True)

    post_publish = post_sub.add_parser("publish", help="Publish a post")
    post_publish.add_argument("text", help="Post text content")
    post_publish.add_argument("--confirm", action="store_true", help="Actually publish (default: dry-run)")
    post_publish.add_argument("--yes", action="store_true", help="Skip interactive confirmation (Agent mode)")

    post_chain = post_sub.add_parser("publish-chain", help="Publish a thread chain")
    post_chain.add_argument("file", help="Input file (- for stdin)")
    post_chain.add_argument("--confirm", action="store_true")
    post_chain.add_argument("--yes", action="store_true")
    post_chain.add_argument(
        "--on-failure",
        choices=["stop", "retry", "rollback"],
        default="stop",
        help="Mid-chain failure policy (Level 1 only implements 'stop')",
    )

    # reply
    reply = subparsers.add_parser("reply", help="Reply to an existing post")
    reply.add_argument("post_id", help="Parent post ID")
    reply.add_argument("text", help="Reply text")
    reply.add_argument("--confirm", action="store_true")
    reply.add_argument("--yes", action="store_true")

    return parser


# Dispatch table: resource.action → handler
COMMANDS: dict[str, callable] = {}


def _register(key: str):
    """Decorator 註冊子命令 handler。"""
    def _wrap(fn):
        COMMANDS[key] = fn
        return fn
    return _wrap


@_register("posts.search")
def cmd_posts_search(args) -> int:
    """threads posts search — 批次 B 實作。"""
    error("posts search: not implemented in batch A (pending batch B)", exit_code=2)


@_register("post.publish")
def cmd_post_publish(args) -> int:
    """threads post publish — Task 6 實作。"""
    error("post publish: not implemented yet (pending task)", exit_code=2)


@_register("post.publish-chain")
def cmd_post_publish_chain(args) -> int:
    """threads post publish-chain — Task 8 實作。"""
    error("post publish-chain: not implemented yet (pending task)", exit_code=2)


@_register("reply")
def cmd_reply(args) -> int:
    """threads reply — Task 7 實作。"""
    error("reply: not implemented yet (pending task)", exit_code=2)


def main(argv: list[str] | None = None) -> int:
    """CLI 入口。"""
    parser = _build_parser()
    args = parser.parse_args(argv)

    # 沒指定 resource → 印 help
    if args.resource is None:
        parser.print_help()
        return 0

    # 組 dispatch key（defensive：reply 沒有 action 屬性）
    if args.resource == "reply":
        key = "reply"
    else:
        action = getattr(args, "action", None)
        if action is None:
            # 理論上 subparsers required=True 會先攔下，但加保險
            error(f"Missing action for resource '{args.resource}'", exit_code=2)
        key = f"{args.resource}.{action}"

    handler = COMMANDS.get(key)
    if handler is None:
        error(f"Unknown command: {key}", exit_code=2)
    return handler(args) or 0


if __name__ == "__main__":
    sys.exit(main())
```

**關鍵差異 vs v1.0**：
- 頂部 `os.environ.setdefault` → `sys.stdout.reconfigure(...)`（runtime 有效）
- 只在 `sys.platform == "win32"` 做 reconfigure
- dispatch key 用 `getattr(args, "action", None)` 防 AttributeError
- `argparse --json` help 加註「batch A: parsed but inert」

- [ ] **Step 6: Run test — expect pass**

Run: `pytest tests/test_threads_cli.py -v`
Expected: 兩個 test 都 PASS。

- [ ] **Step 7: 手動驗證**

Run:
```bash
threads --version
threads --help
threads posts search "AI"
threads post publish "測試"
```

Expected:
- `--version` 印 `threads 0.1.0`
- `--help` 列出 posts / post / reply 三個 resource
- 子命令執行回 `[ERROR] ... not implemented ...` + exit 2

- [ ] **Step 8: Commit**

```bash
git add threads_cli/ tests/test_threads_cli.py
git commit -m "feat(cli): threads CLI 骨架 + dispatch table

- threads_cli/ package 建立於 repo root
- cli.py 用 dispatch table 註冊 handlers（利未來 click 遷移）
- output.py: emit / error / warn；ASCII 前綴（Windows cp950 安全）
- 所有子命令目前回 '[ERROR] not implemented' + exit 2
- Windows UTF-8 用 sys.stdout.reconfigure（setdefault 對 runtime 無效）
- dispatch key 用 getattr(args, 'action', None) 防 reply 缺屬性

驗證：
- threads --version / --help 已可用
- pytest tests/test_threads_cli.py 通過"
```

---

## Task 2: publisher.publish_text — 單則發文

從 `scripts/demo_publish_reply.py` step 1-2 抽出。純邏輯層，不含 CLI。

**Files:**
- Create: `./publisher.py`
- Create: `./tests/test_publisher.py`

- [ ] **Step 1: 寫 failing test**

檔案 `./tests/test_publisher.py`：

```python
"""publisher 模組測試（mock 所有 API 呼叫）。"""

from unittest.mock import patch, MagicMock

import pytest


def test_publish_text_success():
    """Step 1 建 container + Step 2 publish 成功。"""
    from threads_pipeline.publisher import publish_text

    mock_step1 = MagicMock()
    mock_step1.status_code = 200
    mock_step1.json.return_value = {"id": "CONTAINER_123"}

    mock_step2 = MagicMock()
    mock_step2.status_code = 200
    mock_step2.json.return_value = {"id": "POST_456"}

    with patch("threads_pipeline.publisher.requests.post", side_effect=[mock_step1, mock_step2]):
        post_id = publish_text("測試文字", token="fake_token")

    assert post_id == "POST_456"


def test_publish_text_step1_fail():
    """Step 1 失敗應 raise，不呼叫 step 2。"""
    from threads_pipeline.publisher import publish_text, PublishError

    mock_fail = MagicMock()
    mock_fail.status_code = 400
    mock_fail.json.return_value = {"error": {"message": "Invalid text"}}

    with patch("threads_pipeline.publisher.requests.post", return_value=mock_fail) as mocked:
        with pytest.raises(PublishError):
            publish_text("", token="fake_token")

    assert mocked.call_count == 1


def test_publish_text_step2_fail_orphan_container():
    """Step 2 失敗應在錯誤訊息包含 container_id（孤兒 container）。"""
    from threads_pipeline.publisher import publish_text, PublishError

    mock_step1 = MagicMock()
    mock_step1.status_code = 200
    mock_step1.json.return_value = {"id": "CONTAINER_999"}

    mock_step2 = MagicMock()
    mock_step2.status_code = 500
    mock_step2.json.return_value = {"error": {"message": "Server error"}}

    with patch("threads_pipeline.publisher.requests.post", side_effect=[mock_step1, mock_step2]):
        with pytest.raises(PublishError) as exc_info:
            publish_text("ok text", token="fake_token")

    assert "CONTAINER_999" in str(exc_info.value)


def test_publish_text_error_not_dict():
    """若 body['error'] 非 dict（如字串 / null），不該 AttributeError crash。"""
    from threads_pipeline.publisher import publish_text, PublishError

    mock_fail = MagicMock()
    mock_fail.status_code = 400
    mock_fail.json.return_value = {"error": "some raw string error"}

    with patch("threads_pipeline.publisher.requests.post", return_value=mock_fail):
        with pytest.raises(PublishError):
            publish_text("x", token="fake")


def test_publish_text_no_token_raises():
    """未傳 token 且 env 無 token 時 raise。"""
    from threads_pipeline.publisher import publish_text, PublishError

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(PublishError, match="TOKEN"):
            publish_text("x")
```

- [ ] **Step 2: Run — expect fail**

Run: `pytest tests/test_publisher.py -v`
Expected: FAIL — `No module named threads_pipeline.publisher`

- [ ] **Step 3: 實作 publisher.py**

檔案 `./publisher.py`：

```python
"""Threads API 發文邏輯層 — publish / reply / chain。

對應 Threads API 兩階段流程：
- Step 1: POST /me/threads （建立 container）
- Step 2: POST /me/threads_publish （publish container）

Reply 跟 publish 共用流程，差別在 Step 1 多一個 reply_to_id 參數。
"""

import os
from typing import Optional

import requests

THREADS_API_BASE = "https://graph.threads.net/v1.0"


class PublishError(Exception):
    """發文失敗的 exception。"""
    pass


def _post(url: str, params: dict, timeout: int = 30) -> dict:
    """POST 並回傳 JSON，失敗 raise PublishError 帶原始錯誤。"""
    try:
        resp = requests.post(url, params=params, timeout=timeout)
    except requests.exceptions.RequestException as e:
        raise PublishError(f"Network error: {e}") from e

    try:
        body = resp.json()
    except ValueError:
        body = {"raw": resp.text}

    if resp.status_code != 200:
        # 防禦性：body["error"] 可能不是 dict（API 有時回 string / null）
        err = body.get("error")
        if isinstance(err, dict):
            err_msg = err.get("message", "Unknown error")
        elif err:
            err_msg = str(err)
        else:
            err_msg = "Unknown error"
        raise PublishError(f"API {resp.status_code}: {err_msg}")
    return body


def publish_text(
    text: str,
    *,
    token: Optional[str] = None,
    reply_to_id: Optional[str] = None,
) -> str:
    """發一則純文字貼文（或回覆），回傳 post_id。

    Args:
        text: 貼文文字內容
        token: Threads access token；None 時從 THREADS_ACCESS_TOKEN 讀
        reply_to_id: 若提供，發為回覆（reply to 該 post_id）

    Returns:
        發出的 post_id

    Raises:
        PublishError: 任一 step 失敗 / token 缺失
    """
    token = token or os.environ.get("THREADS_ACCESS_TOKEN", "")
    if not token:
        raise PublishError("THREADS_ACCESS_TOKEN not set")

    # Step 1: 建立 container
    step1_params = {
        "access_token": token,
        "media_type": "TEXT",
        "text": text,
    }
    if reply_to_id:
        step1_params["reply_to_id"] = reply_to_id

    step1 = _post(f"{THREADS_API_BASE}/me/threads", step1_params)
    container_id = step1.get("id")
    if not container_id:
        raise PublishError(f"Step 1 returned no container ID: {step1}")

    # Step 2: publish
    step2_params = {
        "access_token": token,
        "creation_id": container_id,
    }
    try:
        step2 = _post(f"{THREADS_API_BASE}/me/threads_publish", step2_params)
    except PublishError as e:
        raise PublishError(
            f"Step 2 failed (orphan container_id={container_id}): {e}"
        ) from e

    post_id = step2.get("id")
    if not post_id:
        raise PublishError(f"Step 2 returned no post ID (container_id={container_id}): {step2}")
    return post_id
```

**關鍵差異 vs v1.0**：
- `_post()` 裡的 error 解析加 `isinstance(err, dict)` 防禦

- [ ] **Step 4: Run — expect pass**

Run: `pytest tests/test_publisher.py -v`
Expected: 5 tests PASS。

- [ ] **Step 5: Commit**

```bash
git add publisher.py tests/test_publisher.py
git commit -m "feat(publisher): publish_text — 兩階段發文 API 封裝

- Step 1: POST /me/threads 建立 container
- Step 2: POST /me/threads_publish 發布
- 支援 reply_to_id 參數（reply 共用此函式）
- _post() 的 error 解析加 isinstance 防禦（body['error'] 可能非 dict）
- Step 2 失敗時錯誤訊息含 container_id（孤兒標記）

測試：
- step1+step2 皆成功
- step1 失敗不呼叫 step2
- step2 失敗錯誤訊息含 container_id
- body['error'] 為字串時不 crash
- Token 缺失 raise PublishError"
```

---

## Task 3: publisher.reply_to — 回覆既有貼文

薄薄一層 wrapper，複用 `publish_text` 的 `reply_to_id` 參數。

**Files:**
- Modify: `./publisher.py`
- Modify: `./tests/test_publisher.py`

- [ ] **Step 1: 寫 failing test**

在 `./tests/test_publisher.py` 加：

```python
def test_reply_to_passes_reply_to_id():
    """reply_to 應把 post_id 傳成 reply_to_id 給 publish_text。"""
    from threads_pipeline.publisher import reply_to

    with patch("threads_pipeline.publisher.publish_text") as mock_pub:
        mock_pub.return_value = "REPLY_POST_789"
        result = reply_to("PARENT_POST_123", "我的回覆", token="fake")

    assert result == "REPLY_POST_789"
    mock_pub.assert_called_once_with(
        "我的回覆",
        token="fake",
        reply_to_id="PARENT_POST_123",
    )


def test_reply_to_requires_parent_id():
    """reply_to 不接受空 post_id。"""
    from threads_pipeline.publisher import reply_to, PublishError

    with pytest.raises(PublishError, match="post_id"):
        reply_to("", "text", token="fake")
```

- [ ] **Step 2: Run — expect fail**

Run: `pytest tests/test_publisher.py::test_reply_to_passes_reply_to_id tests/test_publisher.py::test_reply_to_requires_parent_id -v`
Expected: FAIL。

- [ ] **Step 3: 實作 reply_to**

在 `./publisher.py` 尾部加：

```python
def reply_to(
    parent_post_id: str,
    text: str,
    *,
    token: Optional[str] = None,
) -> str:
    """回覆既有貼文，回傳回覆的 post_id。

    Args:
        parent_post_id: 要回覆的目標 post ID
        text: 回覆文字內容
        token: Threads access token；None 時從環境讀

    Returns:
        回覆貼文的 post_id

    Raises:
        PublishError: parent_post_id 為空或 API 失敗
    """
    if not parent_post_id:
        raise PublishError("reply_to requires non-empty post_id")
    return publish_text(text, token=token, reply_to_id=parent_post_id)
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest tests/test_publisher.py -v`
Expected: 7 tests PASS（5 既有 + 2 新）。

- [ ] **Step 5: Commit**

```bash
git add publisher.py tests/test_publisher.py
git commit -m "feat(publisher): reply_to — 回覆既有貼文

- 透過 publish_text 的 reply_to_id 參數實作
- parent_post_id 為空時拒絕（PublishError）
- Threads API 無專屬 reply endpoint，走 /me/threads + reply_to_id 兩階段流程

測試：
- 參數傳遞正確
- 空 parent_post_id 拒絕"
```

---

## Task 4: publisher.publish_chain — 串文發文

組合 `publish_text` + `reply_to`，階梯式串連。

**Files:**
- Modify: `./publisher.py`
- Modify: `./tests/test_publisher.py`

- [ ] **Step 1: 寫 failing tests**

在 `./tests/test_publisher.py` 加：

```python
def test_publish_chain_success_3_posts():
    """3 則串文：第 1 則用 publish，後續 reply 到前一則（階梯式）。"""
    from threads_pipeline.publisher import publish_chain

    with patch("threads_pipeline.publisher.publish_text") as mock_pub, \
         patch("threads_pipeline.publisher.reply_to") as mock_rep:
        mock_pub.return_value = "POST_1"
        mock_rep.side_effect = ["POST_2", "POST_3"]

        ids = publish_chain(["第 1 則", "第 2 則", "第 3 則"], token="fake")

    assert ids == ["POST_1", "POST_2", "POST_3"]
    mock_pub.assert_called_once_with("第 1 則", token="fake")
    # 第 2 則 reply 到 POST_1
    assert mock_rep.call_args_list[0].args == ("POST_1", "第 2 則")
    # 第 3 則 reply 到 POST_2（階梯式，不是都 reply 到 POST_1）
    assert mock_rep.call_args_list[1].args == ("POST_2", "第 3 則")


def test_publish_chain_preflight_length_all_or_nothing():
    """任一則超過 500 字元 → 拒絕整串，零 API 呼叫。"""
    from threads_pipeline.publisher import publish_chain, PublishError

    with patch("threads_pipeline.publisher.publish_text") as mock_pub, \
         patch("threads_pipeline.publisher.reply_to") as mock_rep:
        with pytest.raises(PublishError, match="500"):
            publish_chain(["ok", "x" * 501, "ok"], token="fake")

    assert mock_pub.call_count == 0
    assert mock_rep.call_count == 0


def test_publish_chain_boundary_500_chars_ok():
    """剛好 500 字元應可通過 pre-flight（邊界正確性）。"""
    from threads_pipeline.publisher import publish_chain

    with patch("threads_pipeline.publisher.publish_text", return_value="POST_1"):
        result = publish_chain(["x" * 500], token="fake")
    assert result == ["POST_1"]


def test_publish_chain_opener_failure_raises_plain_publisherror():
    """第 1 則就失敗 → 拋 plain PublishError，不是 ChainMidwayError。

    理由：沒有 '已發' 需要回報，語義上不是 midway。
    """
    from threads_pipeline.publisher import publish_chain, PublishError, ChainMidwayError

    with patch("threads_pipeline.publisher.publish_text", side_effect=PublishError("opener fail")):
        with pytest.raises(PublishError) as exc_info:
            publish_chain(["a", "b", "c"], token="fake")

    # 必須是 plain PublishError，不是 ChainMidwayError
    assert not isinstance(exc_info.value, ChainMidwayError)


def test_publish_chain_midway_failure_reports_posted_ids():
    """第 3 則失敗 → ChainMidwayError 含已發的 IDs。"""
    from threads_pipeline.publisher import publish_chain, PublishError, ChainMidwayError

    with patch("threads_pipeline.publisher.publish_text") as mock_pub, \
         patch("threads_pipeline.publisher.reply_to") as mock_rep:
        mock_pub.return_value = "POST_1"
        mock_rep.side_effect = ["POST_2", PublishError("API 500")]

        with pytest.raises(ChainMidwayError) as exc_info:
            publish_chain(["a", "b", "c"], token="fake")

    assert exc_info.value.posted_ids == ["POST_1", "POST_2"]
    assert exc_info.value.failed_index == 2
    assert "API 500" in str(exc_info.value.cause)


def test_publish_chain_on_failure_retry_not_implemented():
    """on_failure=retry 應 raise NotImplementedError。"""
    from threads_pipeline.publisher import publish_chain

    with pytest.raises(NotImplementedError, match="retry"):
        publish_chain(["a"], token="fake", on_failure="retry")


def test_publish_chain_on_failure_rollback_not_implemented():
    """on_failure=rollback 應 raise NotImplementedError。"""
    from threads_pipeline.publisher import publish_chain

    with pytest.raises(NotImplementedError, match="rollback"):
        publish_chain(["a"], token="fake", on_failure="rollback")


def test_publish_chain_empty_list():
    """空清單應拒絕。"""
    from threads_pipeline.publisher import publish_chain, PublishError

    with pytest.raises(PublishError, match="empty"):
        publish_chain([], token="fake")
```

- [ ] **Step 2: Run — expect fail**

Run: `pytest tests/test_publisher.py -v`
Expected: 8 新 test FAIL。

- [ ] **Step 3: 實作 publish_chain + ChainMidwayError**

在 `./publisher.py` 尾部加：

```python
MAX_POST_LENGTH = 500  # Threads 平台單則字數上限


class ChainMidwayError(PublishError):
    """串文半途失敗的 exception，攜帶已發 ID 與失敗位置。

    注意：ChainMidwayError IS-A PublishError。
    CLI 層 catch 時務必 subclass 在前、parent 在後，否則 ChainMidwayError
    會被 PublishError branch 吞掉而失去 posted_ids 資訊。
    """

    def __init__(
        self,
        posted_ids: list[str],
        failed_index: int,
        cause: Exception,
    ):
        self.posted_ids = posted_ids
        self.failed_index = failed_index
        self.cause = cause
        super().__init__(
            f"Chain failed at post {failed_index + 1}: "
            f"already posted IDs={posted_ids}, cause={cause}"
        )


def publish_chain(
    texts: list[str],
    *,
    token: Optional[str] = None,
    on_failure: str = "stop",
) -> list[str]:
    """發串文（階梯式 reply 串連），回傳所有 post ID（含 opener）。

    Args:
        texts: 每則一項的字串 list
        token: Threads access token
        on_failure: 半途失敗策略；目前只實作 "stop"；retry / rollback 保留 flag
            但 raise NotImplementedError

    Returns:
        post_ids list，依序對應 texts

    Raises:
        PublishError: 預檢查失敗（空清單、任一則超 500 字）
                     或 opener（第 1 則）失敗（不是 midway）
        ChainMidwayError: opener 之後中途 API 失敗，帶已發 IDs
        NotImplementedError: on_failure=retry 或 rollback
    """
    if on_failure != "stop":
        raise NotImplementedError(
            f"on_failure={on_failure!r} not implemented in Level 1 (only 'stop')"
        )

    if not texts:
        raise PublishError("publish_chain: texts list is empty")

    # Pre-flight 字數檢查（全有或全無）
    for i, text in enumerate(texts):
        if len(text) > MAX_POST_LENGTH:
            raise PublishError(
                f"publish_chain: post {i + 1} exceeds {MAX_POST_LENGTH} chars "
                f"({len(text)} chars)"
            )

    posted_ids: list[str] = []
    try:
        # 第 1 則：獨立 publish
        first_id = publish_text(texts[0], token=token)
        posted_ids.append(first_id)

        # 後續：階梯式 reply 到前一則
        parent_id = first_id
        for text in texts[1:]:
            reply_id = reply_to(parent_id, text, token=token)
            posted_ids.append(reply_id)
            parent_id = reply_id
    except PublishError as e:
        # Opener 就失敗 → 沒有 "已發"，拋 plain PublishError 讓上層處理
        if not posted_ids:
            raise
        # 真 midway → 升級為 ChainMidwayError 帶 posted_ids
        raise ChainMidwayError(
            posted_ids=posted_ids,
            failed_index=len(posted_ids),
            cause=e,
        ) from e

    return posted_ids
```

**關鍵差異 vs v1.0**：
- Opener 失敗時 re-raise plain PublishError（不升級為 ChainMidwayError）
- ChainMidwayError docstring 警告 catch 順序
- 加 500-char boundary test

- [ ] **Step 4: Run — expect pass**

Run: `pytest tests/test_publisher.py -v`
Expected: 全部 15 個 test PASS（7 既有 + 8 新）。

- [ ] **Step 5: Commit**

```bash
git add publisher.py tests/test_publisher.py
git commit -m "feat(publisher): publish_chain — 串文發文（階梯式 reply）

- 第 1 則 publish，後續 reply 到前一則（階梯式）
- Pre-flight 字數檢查：任一則超 500 拒絕整串（零 API 呼叫）
- Opener（第 1 則）失敗 → 拋 plain PublishError（語義上不是 midway）
- 真 midway 失敗 → ChainMidwayError（含 posted_ids、failed_index）
- on_failure flag 預留 stop/retry/rollback；retry/rollback raise NotImplementedError
- ChainMidwayError IS-A PublishError，docstring 警告 CLI catch 順序

測試：
- 3 則成功（階梯式驗證）
- pre-flight 拒絕 + 500 字邊界
- opener 失敗拋 plain PublishError
- midway 失敗帶 posted_ids
- retry/rollback NotImplementedError
- 空清單拒絕"
```

---

## Task 5: CLI safety — Token / confirm / yes / TTY

安全層 helpers。

**Files:**
- Create: `./threads_cli/safety.py`
- Create: `./tests/test_cli_safety.py`

- [ ] **Step 1: 寫 failing tests**

檔案 `./tests/test_cli_safety.py`：

```python
"""CLI 安全層測試。"""

from unittest.mock import patch

import pytest


def test_require_token_present():
    """Token 存在應回傳 token 值。"""
    from threads_pipeline.threads_cli.safety import require_token

    with patch.dict("os.environ", {"THREADS_ACCESS_TOKEN": "abc123"}):
        assert require_token() == "abc123"


def test_require_token_missing_exits_1():
    """Token 缺失應 exit 1。"""
    from threads_pipeline.threads_cli.safety import require_token

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(SystemExit) as exc_info:
            require_token()
    assert exc_info.value.code == 1


def test_validate_confirm_yes_yes_without_confirm_hard_error():
    """--yes 無 --confirm → exit 2。"""
    from threads_pipeline.threads_cli.safety import validate_confirm_yes

    with pytest.raises(SystemExit) as exc_info:
        validate_confirm_yes(confirm=False, yes=True, is_tty=True)
    assert exc_info.value.code == 2


def test_validate_confirm_yes_nontty_confirm_without_yes_hard_error():
    """非 TTY + --confirm 無 --yes → exit 2。"""
    from threads_pipeline.threads_cli.safety import validate_confirm_yes

    with pytest.raises(SystemExit) as exc_info:
        validate_confirm_yes(confirm=True, yes=False, is_tty=False)
    assert exc_info.value.code == 2


def test_validate_confirm_yes_tty_confirm_without_yes_ok():
    """TTY + --confirm 無 --yes 可執行（會進互動確認）。"""
    from threads_pipeline.threads_cli.safety import validate_confirm_yes

    validate_confirm_yes(confirm=True, yes=False, is_tty=True)  # no raise


def test_validate_confirm_yes_both_ok():
    """--confirm --yes 組合正確。"""
    from threads_pipeline.threads_cli.safety import validate_confirm_yes

    validate_confirm_yes(confirm=True, yes=True, is_tty=False)
    validate_confirm_yes(confirm=True, yes=True, is_tty=True)


def test_validate_confirm_yes_neither_ok():
    """沒 flag（純 dry-run）也合法。"""
    from threads_pipeline.threads_cli.safety import validate_confirm_yes

    validate_confirm_yes(confirm=False, yes=False, is_tty=True)
    validate_confirm_yes(confirm=False, yes=False, is_tty=False)


def test_interactive_confirm_yes_proceeds():
    """使用者輸入 y 應回傳 True。"""
    from threads_pipeline.threads_cli.safety import interactive_confirm

    with patch("builtins.input", return_value="y"):
        assert interactive_confirm() is True


def test_interactive_confirm_n_cancels():
    """使用者輸入 n 或 Enter 應回傳 False。"""
    from threads_pipeline.threads_cli.safety import interactive_confirm

    with patch("builtins.input", return_value=""):
        assert interactive_confirm() is False
    with patch("builtins.input", return_value="n"):
        assert interactive_confirm() is False


def test_interactive_confirm_eof_cancels():
    """EOFError 應視為取消（回 False）。"""
    from threads_pipeline.threads_cli.safety import interactive_confirm

    with patch("builtins.input", side_effect=EOFError):
        assert interactive_confirm() is False
```

- [ ] **Step 2: Run — expect fail**

Run: `pytest tests/test_cli_safety.py -v`
Expected: FAIL — module not found。

- [ ] **Step 3: 實作 safety.py**

檔案 `./threads_cli/safety.py`：

```python
"""CLI 安全層：Token 檢查、--confirm/--yes 驗證、互動確認。"""

import os
import sys


def require_token() -> str:
    """取得 THREADS_ACCESS_TOKEN；缺失則 exit 1。"""
    token = os.environ.get("THREADS_ACCESS_TOKEN", "")
    if not token:
        print(
            "[ERROR] THREADS_ACCESS_TOKEN not set.\n"
            "  Add it to .env or export as environment variable.\n"
            "  Get a token: https://developers.facebook.com/tools/access-token-tool/",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


def validate_confirm_yes(*, confirm: bool, yes: bool, is_tty: bool) -> None:
    """驗證 --confirm / --yes 組合合法性。

    規則：
    - --yes 無 --confirm → hard-error exit 2
    - 非 TTY + --confirm 無 --yes → hard-error exit 2
    - 其他合法組合（含無 flag）→ 返回，不拋例外
    """
    if yes and not confirm:
        print(
            "[ERROR] --yes requires --confirm. "
            "Without --confirm the command runs as dry-run.",
            file=sys.stderr,
        )
        sys.exit(2)

    if confirm and not yes and not is_tty:
        print(
            "[ERROR] --confirm requires --yes in non-interactive environments "
            "(CI / piped input / no TTY).",
            file=sys.stderr,
        )
        sys.exit(2)


def interactive_confirm(prompt: str = "Proceed?") -> bool:
    """TTY 互動確認；預設 N，EOFError / KeyboardInterrupt 視為取消。"""
    try:
        answer = input(f"{prompt} [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n(cancelled)", file=sys.stderr)
        return False
    return answer == "y"
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest tests/test_cli_safety.py -v`
Expected: 10 tests PASS。

- [ ] **Step 5: Commit**

```bash
git add threads_cli/safety.py tests/test_cli_safety.py
git commit -m "feat(cli): safety 層 — Token 檢查 / --confirm --yes 驗證 / 互動確認

- require_token: 缺失 exit 1 + 續期連結
- validate_confirm_yes:
  - --yes 無 --confirm → exit 2
  - 非 TTY + --confirm 無 --yes → exit 2
  - 其他合法
- interactive_confirm: 預設 N，EOFError / KeyboardInterrupt 視為取消
- 所有錯誤訊息用 [ERROR] ASCII 前綴（Windows cp950 安全）

測試：10 個 test 全過"
```

---

## Task 6: threads post publish CLI 指令

接上 publisher.publish_text。

**Files:**
- Modify: `./threads_cli/cli.py`
- Modify: `./tests/test_threads_cli.py`

- [ ] **Step 1: 寫 failing tests**

在 `./tests/test_threads_cli.py` 加：

```python
def test_cli_post_publish_dry_run():
    """無 --confirm 應 dry-run，不呼叫 publisher。"""
    from threads_pipeline.threads_cli.cli import main

    with patch("threads_pipeline.threads_cli.cli.publish_text") as mock_pub, \
         patch("threads_pipeline.threads_cli.cli.require_token", return_value="fake"):
        rc = main(["post", "publish", "測試文字"])

    assert rc == 0
    assert mock_pub.call_count == 0


def test_cli_post_publish_confirm_yes_calls_api():
    """--confirm --yes 應呼叫 publish_text。"""
    from threads_pipeline.threads_cli.cli import main

    with patch("threads_pipeline.threads_cli.cli.publish_text", return_value="POST_ABC") as mock_pub, \
         patch("threads_pipeline.threads_cli.cli.require_token", return_value="fake"):
        rc = main(["post", "publish", "hello", "--confirm", "--yes"])

    assert rc == 0
    mock_pub.assert_called_once()
    assert mock_pub.call_args.args[0] == "hello"


def test_cli_post_publish_yes_without_confirm_exit_2():
    """--yes 無 --confirm → exit 2。"""
    from threads_pipeline.threads_cli.cli import main

    with patch("threads_pipeline.threads_cli.cli.require_token", return_value="fake"):
        with pytest.raises(SystemExit) as exc_info:
            main(["post", "publish", "x", "--yes"])
    assert exc_info.value.code == 2
```

- [ ] **Step 2: Run — expect fail**

Run: `pytest tests/test_threads_cli.py -k post_publish -v`
Expected: FAIL — stub handler。

- [ ] **Step 3: 實作 cmd_post_publish**

修改 `./threads_cli/cli.py`：

**注意**：`import sys` 在 Task 1 已加，不重複。

在頂部 import 區加（既有 import 後面）：

```python
from threads_pipeline.publisher import publish_text, PublishError
from threads_pipeline.threads_cli.safety import (
    require_token,
    validate_confirm_yes,
    interactive_confirm,
)
```

替換既有的 stub `cmd_post_publish`：

```python
@_register("post.publish")
def cmd_post_publish(args) -> int:
    """threads post publish — 發單則貼文。"""
    token = require_token()
    is_tty = sys.stdin.isatty()
    validate_confirm_yes(confirm=args.confirm, yes=args.yes, is_tty=is_tty)

    text = args.text
    char_count = len(text)

    # Dry-run 預設
    if not args.confirm:
        print("[DRY RUN] Would publish:")
        print("---------------------------------")
        print(text)
        print("---------------------------------")
        print(f"Character count: {char_count}")
        print("Add --confirm to actually publish.")
        return 0

    # 互動確認（TTY + --confirm 無 --yes）
    if not args.yes:
        print("About to publish:")
        print("---------------------------------")
        print(text)
        print("---------------------------------")
        print(f"Character count: {char_count}")
        if not interactive_confirm():
            print("(cancelled)")
            return 0

    # 真正發文
    try:
        post_id = publish_text(text, token=token)
    except PublishError as e:
        error(str(e), exit_code=1)  # raises SystemExit, no unreachable return after

    print(f"[OK] Published as post {post_id}")
    return 0
```

**關鍵差異 vs v1.0**：
- 分隔線改 ASCII `---------------------------------`（Windows 安全）
- 成功訊息 `[OK]` 取代 `✓`
- `error()` 後不寫 unreachable `return 1`

- [ ] **Step 4: Run — expect pass**

Run: `pytest tests/test_threads_cli.py -v`
Expected: 全通過。

- [ ] **Step 5: Commit**

```bash
git add threads_cli/cli.py tests/test_threads_cli.py
git commit -m "feat(cli): threads post publish 指令接上 publisher

- 預設 dry-run（印 text + 字數 + 提示）
- --confirm 無 --yes TTY 時互動確認（預設 N）
- --confirm --yes 直接發文
- safety.validate_confirm_yes 處理違規組合
- PublishError → error() exit 1（SystemExit，無 dead code return）
- 分隔線 / 前綴都用 ASCII（Windows cp950 安全）

測試：dry-run / confirm+yes / yes 無 confirm 三個 case"
```

---

## Task 7: threads reply CLI 指令

類似 Task 6，呼叫 `publisher.reply_to`。

**Files:**
- Modify: `./threads_cli/cli.py`
- Modify: `./tests/test_threads_cli.py`

- [ ] **Step 1: 寫 failing tests**

在 `./tests/test_threads_cli.py` 加：

```python
def test_cli_reply_dry_run():
    """reply 無 --confirm 應 dry-run。"""
    from threads_pipeline.threads_cli.cli import main

    with patch("threads_pipeline.threads_cli.cli.reply_to") as mock_rep, \
         patch("threads_pipeline.threads_cli.cli.require_token", return_value="fake"):
        rc = main(["reply", "POST_123", "我的回覆"])

    assert rc == 0
    assert mock_rep.call_count == 0


def test_cli_reply_confirm_yes_calls_api():
    """reply --confirm --yes 應呼叫 reply_to。"""
    from threads_pipeline.threads_cli.cli import main

    with patch("threads_pipeline.threads_cli.cli.reply_to", return_value="REPLY_ABC") as mock_rep, \
         patch("threads_pipeline.threads_cli.cli.require_token", return_value="fake"):
        rc = main(["reply", "POST_123", "回覆", "--confirm", "--yes"])

    assert rc == 0
    mock_rep.assert_called_once()
    assert mock_rep.call_args.args[0] == "POST_123"
    assert mock_rep.call_args.args[1] == "回覆"
```

- [ ] **Step 2: Run — expect fail**

Run: `pytest tests/test_threads_cli.py -k reply -v`
Expected: FAIL。

- [ ] **Step 3: 實作 cmd_reply**

修改 `./threads_cli/cli.py` 頂部 import 加（放在既有 publisher import 後）：

```python
from threads_pipeline.publisher import reply_to
```

（若已寫成 `from threads_pipeline.publisher import publish_text, PublishError`，把它改成 `from threads_pipeline.publisher import publish_text, reply_to, PublishError`）

替換既有 stub `cmd_reply`：

```python
@_register("reply")
def cmd_reply(args) -> int:
    """threads reply <post_id> <text> — 回覆既有貼文。"""
    token = require_token()
    is_tty = sys.stdin.isatty()
    validate_confirm_yes(confirm=args.confirm, yes=args.yes, is_tty=is_tty)

    parent_id = args.post_id
    text = args.text
    char_count = len(text)

    if not args.confirm:
        print(f"[DRY RUN] Would reply to post {parent_id}:")
        print("---------------------------------")
        print(text)
        print("---------------------------------")
        print(f"Character count: {char_count}")
        print("Add --confirm to actually reply.")
        return 0

    if not args.yes:
        print(f"About to reply to post {parent_id}:")
        print("---------------------------------")
        print(text)
        print("---------------------------------")
        if not interactive_confirm():
            print("(cancelled)")
            return 0

    try:
        reply_id = reply_to(parent_id, text, token=token)
    except PublishError as e:
        error(str(e), exit_code=1)  # SystemExit

    print(f"[OK] Reply posted as {reply_id} (parent: {parent_id})")
    return 0
```

- [ ] **Step 4: Run — expect pass**

Run: `pytest tests/test_threads_cli.py -v`
Expected: 全通過。

- [ ] **Step 5: Commit**

```bash
git add threads_cli/cli.py tests/test_threads_cli.py
git commit -m "feat(cli): threads reply 指令接上 publisher.reply_to

- 參數：post_id text
- 預設 dry-run / --confirm 互動 / --yes Agent
- 成功回 '[OK] Reply posted as <id> (parent: <parent>)'

測試：dry-run + confirm+yes 兩個 case"
```

---

## Task 8: threads post publish-chain CLI 指令

**Files:**
- Modify: `./threads_cli/cli.py`
- Modify: `./tests/test_threads_cli.py`
- Create: `./drafts/smoke-test.txt`

- [ ] **Step 1: 建立 drafts/smoke-test.txt**

檔案 `./drafts/smoke-test.txt`：

```
[CLI smoke test] chain post 1 - will delete shortly
[CLI smoke test] chain post 2 - reply to previous
[CLI smoke test] chain post 3 - final reply in chain
```

- [ ] **Step 2: 寫 failing tests**

在 `./tests/test_threads_cli.py` 加：

```python
def test_cli_publish_chain_reads_file(tmp_path):
    """從檔案讀多行，dry-run 印出清單。"""
    from threads_pipeline.threads_cli.cli import main

    chain_file = tmp_path / "chain.txt"
    chain_file.write_text("第一則\n第二則\n第三則\n", encoding="utf-8")

    with patch("threads_pipeline.threads_cli.cli.publish_chain") as mock_chain, \
         patch("threads_pipeline.threads_cli.cli.require_token", return_value="fake"):
        rc = main(["post", "publish-chain", str(chain_file)])

    assert rc == 0
    assert mock_chain.call_count == 0  # dry-run 不呼叫


def test_cli_publish_chain_confirm_yes_calls_api(tmp_path):
    """--confirm --yes 應呼叫 publish_chain。"""
    from threads_pipeline.threads_cli.cli import main

    chain_file = tmp_path / "chain.txt"
    chain_file.write_text("a\nb\nc\n", encoding="utf-8")

    with patch("threads_pipeline.threads_cli.cli.publish_chain", return_value=["1", "2", "3"]) as mock_chain, \
         patch("threads_pipeline.threads_cli.cli.require_token", return_value="fake"):
        rc = main(["post", "publish-chain", str(chain_file), "--confirm", "--yes"])

    assert rc == 0
    mock_chain.assert_called_once()
    assert mock_chain.call_args.args[0] == ["a", "b", "c"]


def test_cli_publish_chain_on_failure_not_stop_exit_2(tmp_path):
    """--on-failure=retry 應因 NotImplementedError 而 exit 2。"""
    from threads_pipeline.threads_cli.cli import main

    chain_file = tmp_path / "chain.txt"
    chain_file.write_text("a\n", encoding="utf-8")

    with patch("threads_pipeline.threads_cli.cli.require_token", return_value="fake"):
        with pytest.raises(SystemExit) as exc_info:
            main(["post", "publish-chain", str(chain_file),
                  "--confirm", "--yes", "--on-failure", "retry"])
    assert exc_info.value.code == 2  # 精確檢查（不是 in (1, 2)）
```

**關鍵差異 vs v1.0**：最後一個 test 把 `in (1, 2)` 收緊成 `== 2`。

- [ ] **Step 3: Run — expect fail**

Run: `pytest tests/test_threads_cli.py -k publish_chain -v`
Expected: FAIL。

- [ ] **Step 4: 實作 cmd_post_publish_chain**

修改 `./threads_cli/cli.py` 頂部 import 加：

```python
from threads_pipeline.publisher import publish_chain, ChainMidwayError
```

（可併到既有 publisher import 一行：`from threads_pipeline.publisher import publish_text, reply_to, publish_chain, PublishError, ChainMidwayError`）

替換既有 stub `cmd_post_publish_chain`：

```python
@_register("post.publish-chain")
def cmd_post_publish_chain(args) -> int:
    """threads post publish-chain FILE — 串文發文。"""
    token = require_token()
    is_tty = sys.stdin.isatty()
    validate_confirm_yes(confirm=args.confirm, yes=args.yes, is_tty=is_tty)

    # 讀取輸入
    if args.file == "-":
        content = sys.stdin.read()
    else:
        try:
            with open(args.file, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            error(f"Cannot read file {args.file}: {e}", exit_code=1)

    # 空行分隔規則：一則 post = 一行，空行忽略
    # 注意：不支援多段落同一則（Level 1 限制）
    texts = [line.strip() for line in content.splitlines() if line.strip()]
    if not texts:
        error("No non-empty lines in input", exit_code=1)

    total_chars = sum(len(t) for t in texts)

    # Dry-run
    if not args.confirm:
        print(f"[DRY RUN] Would publish chain of {len(texts)} posts:")
        print("---------------------------------")
        for i, t in enumerate(texts):
            label = "opener" if i == 0 else "reply"
            print(f"{i + 1}/{len(texts)} ({label}):\t{t} ({len(t)} chars)")
        print("---------------------------------")
        print(f"Total: {len(texts)} posts, {total_chars} chars")
        print(f"On-failure policy: {args.on_failure}")
        print("Add --confirm to actually publish.")
        return 0

    # 互動確認
    if not args.yes:
        print(f"About to publish chain of {len(texts)} posts:")
        for i, t in enumerate(texts):
            preview = t[:60] + ("..." if len(t) > 60 else "")
            print(f"  {i + 1}. {preview}")
        if not interactive_confirm():
            print("(cancelled)")
            return 0

    # 真正發
    # IMPORTANT: ChainMidwayError IS-A PublishError — 保持 subclass 在前
    try:
        post_ids = publish_chain(texts, token=token, on_failure=args.on_failure)
    except NotImplementedError as e:
        error(str(e), exit_code=2)
    except ChainMidwayError as e:
        print(f"[ERROR] Chain failed at post {e.failed_index + 1}", file=sys.stderr)
        print(f"  Already posted IDs: {e.posted_ids}", file=sys.stderr)
        print(f"  Cause: {e.cause}", file=sys.stderr)
        print(f"  Recovery: manually delete or continue from post {e.failed_index + 1}", file=sys.stderr)
        return 1
    except PublishError as e:
        error(str(e), exit_code=1)

    print(f"[OK] Published chain of {len(post_ids)} posts:")
    for i, pid in enumerate(post_ids):
        print(f"  {i + 1}. {pid}")
    return 0
```

**關鍵差異 vs v1.0**：
- `error()` 後移除 unreachable `return 1/2`
- 分隔線改 ASCII
- 加註解提醒 ChainMidwayError subclass 順序
- 空行分隔規則寫進註解（SKILL.md 也會提）

- [ ] **Step 5: Run — expect pass**

Run: `pytest tests/test_threads_cli.py -v`
Expected: 全通過。

- [ ] **Step 6: Commit**

```bash
git add threads_cli/cli.py tests/test_threads_cli.py drafts/smoke-test.txt
git commit -m "feat(cli): threads post publish-chain 指令接上 publisher.publish_chain

- 讀檔（或 - 讀 stdin）、每行一則、空行自動濾除
- dry-run 印 opener/reply 標籤 + 字數 + on-failure policy
- --confirm 互動確認、--yes Agent 模式
- ChainMidwayError → 印 posted_ids + failed_index + 恢復提示 + exit 1
- NotImplementedError（--on-failure retry/rollback）→ exit 2
- except 順序：ChainMidwayError → PublishError（subclass 在前，避免誤吞）
- drafts/smoke-test.txt 提供 3 行測試檔（ASCII 內容）

測試：檔案讀取 dry-run / confirm+yes / on-failure=retry 三個 case
      最後一個 test 用 == 2（精確檢查）"
```

---

## Task 9: SKILL.md 最小版

**Files:**
- Create: `./threads_cli/SKILL.md`

- [ ] **Step 1: 建立 SKILL.md**

檔案 `./threads_cli/SKILL.md`：

```markdown
---
name: threads-cli
description: Threads API CLI — publish posts, reply, publish thread chains. Supports Agent mode via --confirm --yes.
---

## 指令索引

**唯讀（批次 A 尚未實作，批次 B 補齊）：**
- `threads posts search <keyword>` — 搜尋貼文
- `threads posts list --recent N` — 列自己最近貼文
- `threads post insights <id>` — 讀單篇數據
- `threads post replies <id>` — 列回覆
- `threads account info` — 帳號資訊
- `threads account insights` — 帳號數據

**寫入（批次 A 已實作）：**
- `threads post publish <text>` — 發一則貼文
- `threads reply <post_id> <text>` — 回覆既有貼文
- `threads post publish-chain <file>` — 發串文（每行一則，空行濾除）

**系統：**
- `threads --version`
- `threads --help`
- `threads <subcommand> --help`

## 安全契約（Agent 模式）

寫入指令必須用 `--confirm --yes` 才會真的執行：
- `threads post publish "..." --confirm --yes`
- `threads reply <id> "..." --confirm --yes`
- `threads post publish-chain file.txt --confirm --yes`

**規則**：
- 沒加 `--confirm`：dry-run（只印會發什麼）
- 有 `--confirm` 沒 `--yes`（非 TTY 環境）：**hard-error exit 2**
- `--yes` 沒 `--confirm`：**hard-error exit 2**
- Token 缺失：exit 1

## 輸出格式

查詢指令支援 `--json`。批次 A 的 `--json` flag 已註冊但 inert（寫入指令無 JSON 輸出）。批次 B 實作唯讀指令時啟用。

## publish-chain 輸入格式

每行一則貼文，空行會被濾除。目前不支援「多段落同一則」— 若需要，用 `\n` 轉義字元或等批次 B 評估進階輸入格式。

## 已知限制

- 中文關鍵字搜尋通常回 0 筆（Threads API 限制）
- `--limit` 上限 25（專案設定於 `threads_client.py:75`；API 真正上限 50）
- `--author` flag 不提供（Threads API 忽略此參數）
- 字數以 Python `len()` 計算，可能與 Threads 平台顯示略有差異（emoji ZWJ 等）
- 詳見 `docs/dev/api-exploration-results.md`

## Exit codes

| Code | 情境 |
|---|---|
| 0 | 成功 / dry-run 完成 / 使用者取消 |
| 1 | API 失敗 / 網路錯誤 / Token 缺失 / 檔案讀取失敗 / ChainMidwayError |
| 2 | 使用者用法錯誤（--confirm --yes 組合錯誤、--on-failure=retry/rollback 未實作、unknown subcommand） |

## Token 權限需求

寫入指令需要 Threads access token 包含 `threads_content_publish` 權限。若 token scope 不足會回 API 400 錯誤。Token 取得 / 續期：https://developers.facebook.com/tools/access-token-tool/

## 詳細文檔

- 完整 spec：`docs/superpowers/specs/2026-04-15-threads-cli-packaging-design.md`
- API 實測：`docs/dev/api-exploration-results.md`
- 架構研究：`docs/dev/cli-anything-research.md`
```

- [ ] **Step 2: Commit**

```bash
git add threads_cli/SKILL.md
git commit -m "docs(cli): SKILL.md 最小版 — Agent 使用說明

內容：
- 指令索引（批次 A 已實作 + 批次 B 待做）
- 安全契約（--confirm --yes 規則）
- 輸出格式（--json 批次 A inert 聲明）
- publish-chain 輸入格式（每行一則、空行濾除、不支援多段落）
- 已知限制（中文搜尋、limit 25、--author、字數計算差異）
- Exit codes 對照表
- Token 權限需求（threads_content_publish scope）
- 詳細文檔連結"
```

---

## Task 10: CLAUDE.md Commands 區塊更新

**Files:**
- Modify: `./CLAUDE.md`

- [ ] **Step 1: 找現有 Commands 區塊**

Run: `grep -n "^## Commands" CLAUDE.md` 找起始行。

- [ ] **Step 2: 替換 Commands 區塊**

在 `CLAUDE.md` 的 `## Commands` 底下（至下一個 `##` 之前），整段替換為：

````markdown
## Commands

### 新版 CLI（推薦）

```bash
# 一次性安裝（開發模式）
pip install -e ".[dev]"

# Advisor
threads-advisor plan "題目"
threads-advisor review drafts/x.txt
threads-advisor analyze
threads-advisor list-frameworks

# Threads API 操作（寫入指令預設 dry-run）
threads post publish "測試文字"                       # dry-run
threads post publish "測試文字" --confirm --yes       # 真發（Agent 模式）
threads reply <post_id> "回覆內容" --confirm --yes
threads post publish-chain drafts/smoke-test.txt --confirm --yes

# 每日 pipeline（不 CLI 化）
$env:PYTHONUTF8=1; python -m threads_pipeline.main   # PowerShell
PYTHONUTF8=1 python -m threads_pipeline.main          # bash
```

### 舊版（相容性保留）

```bash
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor plan "題目"
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor review drafts/my-post.txt
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor review --text "草稿文字"
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor analyze
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor list-frameworks
```

### 測試

```bash
python -m pytest
python -m pytest tests/test_threads_cli.py
python3 scripts/api_explorer.py
$env:PYTHONUTF8=1; python -m pytest tests/evals/ --run-llm-evals
```
````

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(claude): 更新 Commands 區塊為雙軌並列

- 新增【新版 CLI（推薦）】section
- 既有 python -m 用法保留在【舊版（相容性保留）】
- 加 pip install -e \".[dev]\" 一次性安裝指令"
```

---

## Task 11: 手動 Smoke Test（實發 + 刪除）

**Files:** 無（執行步驟）

- [ ] **Step 0: Token scope 前置檢查**

Smoke test 需要 Token 包含 `threads_content_publish` 權限。確認步驟：

```bash
# 讀帳號基本資訊，若 token 無效會回 401
curl -s "https://graph.threads.net/v1.0/me?access_token=$THREADS_ACCESS_TOKEN"
```

Expected: 回 `{"id": "...", "username": "..."}` 等資料。

若無 scope，到 Graph API Explorer 重產一個含 `threads_content_publish` 權限的 token，更新 `.env`。

**沒這一步，以下所有真發 API 測試都會失敗並給 confusing 400 錯誤**。

- [ ] **Step 1: 全域回歸檢查**

Run: `pytest -v`
Expected: 全部通過。

任一 test 紅就 revert 到最後通過的 commit 再除錯。

- [ ] **Step 2: 指令存在性檢查**

Run:
```bash
where threads-advisor
where threads
where cli-anything-threads
```
Expected: 三個都回 .exe 路徑。

- [ ] **Step 3: 雙軌對照（list-frameworks 輸出應一致）**

Run（bash 或 Git Bash）:
```bash
threads-advisor list-frameworks > new.txt
python -m threads_pipeline.advisor list-frameworks > old.txt
diff new.txt old.txt
rm new.txt old.txt
```

PowerShell 等效：
```powershell
threads-advisor list-frameworks | Out-File new.txt
python -m threads_pipeline.advisor list-frameworks | Out-File old.txt
Compare-Object (Get-Content new.txt) (Get-Content old.txt)
Remove-Item new.txt, old.txt
```

Expected: 無差異。

- [ ] **Step 4: 寫入指令 dry-run 驗證**

Run: `threads post publish "[smoke test] dry run check"`
Expected:
- 印 `[DRY RUN] Would publish:` + 文字 + 字數
- exit 0
- **到 Threads 網站確認沒有新貼文**

- [ ] **Step 5: Token 保護驗證**

PowerShell:
```powershell
$env:THREADS_ACCESS_TOKEN=""; threads post publish "x"
# 之後記得 $env:THREADS_ACCESS_TOKEN = "<原 token>" 復原
```

Bash（Git Bash 在 Windows）：
```bash
THREADS_ACCESS_TOKEN= threads post publish "x"
```

Expected: exit 1 + `[ERROR] THREADS_ACCESS_TOKEN not set` + 續期連結。

- [ ] **Step 6: 非 TTY + --confirm 無 --yes hard-error**

Run: `echo y | threads post publish "x" --confirm`
Expected: exit 2 + `[ERROR] --confirm requires --yes in non-interactive environments`。

- [ ] **Step 7: --yes 無 --confirm hard-error**

Run: `threads post publish "x" --yes`
Expected: exit 2 + `[ERROR] --yes requires --confirm`。

- [ ] **Step 8: 實發單則貼文 + 刪除**

Run: `threads post publish "[CLI smoke test] single post - please ignore" --confirm --yes`
Expected: 印 `[OK] Published as post <post_id>`，記下 post_id。

**等 5-10 秒**（API → 顯示有延遲），到 Threads 網站確認貼文存在。

**刪除**（用 demo_publish_reply.py 示範的 DELETE 最快）：

```bash
# 替換 <POST_ID>、確認 $THREADS_ACCESS_TOKEN 可用
curl -s -X DELETE "https://graph.threads.net/v1.0/<POST_ID>?access_token=$THREADS_ACCESS_TOKEN"
```

PowerShell:
```powershell
Invoke-WebRequest -Method DELETE -Uri "https://graph.threads.net/v1.0/<POST_ID>?access_token=$env:THREADS_ACCESS_TOKEN"
```

到網站確認刪除成功。

- [ ] **Step 9: 實發回覆 + 刪除（reply smoke test）**

先發一則 parent：
```bash
threads post publish "[CLI smoke test] parent for reply - please ignore" --confirm --yes
# 記下 parent_id
```

回覆它：
```bash
threads reply <parent_id> "[CLI smoke test] reply content" --confirm --yes
# 記下 reply_id
```

到 Threads 網站確認 reply 掛在 parent 下方。

**刪除兩則**（用上面的 curl / Invoke-WebRequest，逐一刪）。

- [ ] **Step 10: 實發 3 則串文 + 刪除**

Run: `threads post publish-chain drafts/smoke-test.txt --confirm --yes`
Expected: 印 `[OK] Published chain of 3 posts:` + 3 個 post_id。

**到 Threads 網站確認**：
- 第 1 則獨立
- 第 2 則是第 1 則的 reply
- 第 3 則是第 2 則的 reply（不是第 1 則的 reply — 這是階梯式，不是 flat）

**手動刪除三則**（逐一用 DELETE API）。有些情況刪第 1 則會連帶刪整串，但不保證 — 建議逐一確認。

- [ ] **Step 11: --on-failure=retry 應回 exit 2**

Run: `threads post publish-chain drafts/smoke-test.txt --confirm --yes --on-failure retry`
Expected: exit 2 + 錯誤訊息含「retry」+「not implemented」。

- [ ] **Step 12: 記錄 smoke test 結果到 handoff**

寫 `docs/superpowers/handoffs/YYYY-MM-DD-threads-cli-smoke.md`（檔名用實際執行日期）：

```markdown
# Threads CLI 批次 A Smoke Test 結果

日期：<實際執行日期>
分支：feat/cli-packaging

## 驗證通過

- [x] Token scope 驗證（threads_content_publish 可用）
- [x] pytest 全綠
- [x] 三個 entry points 指令存在
- [x] list-frameworks 雙軌輸出相同
- [x] dry-run 不真發
- [x] Token 缺失 exit 1
- [x] 非 TTY --confirm 無 --yes exit 2
- [x] --yes 無 --confirm exit 2
- [x] 實發單則 <POST_ID> 成功 → 已刪除
- [x] 實發 reply parent=<PARENT_ID> reply=<REPLY_ID> → 已刪除
- [x] 實發 3 則串文 <IDs> 階梯式驗證 → 已刪除
- [x] --on-failure=retry exit 2

## 備註

<任何值得記錄的異常 / 觀察>
```

- [ ] **Step 13: Commit**

```bash
git add docs/superpowers/handoffs/YYYY-MM-DD-threads-cli-smoke.md
git commit -m "docs(handoff): 批次 A smoke test 通過紀錄

13 項手動驗證全過，測試貼文已手動刪除。"
```

---

## Task 12: 驗收 checklist 對照 + Merge 準備

**Files:** 無（驗收步驟）

- [ ] **Step 1: 對照 spec §575 驗收條件**

打開 `docs/superpowers/specs/2026-04-15-threads-cli-packaging-design.md` 驗收條件區，逐項確認：

- [ ] `pyproject.toml` 已建立且 `pip install -e ".[dev]"` 成功（Task 0）
- [ ] 三個指令都能執行（Task 0 + smoke Step 2）
- [ ] 既有 pytest 全通過（Task 0 + smoke Step 1）
- [ ] `tests/test_threads_cli.py` 新測試通過（Task 1、6、7、8）
- [ ] list-frameworks 輸出雙軌一致（smoke Step 3）
- [ ] publish 無 --confirm 絕對不發（smoke Step 4）
- [ ] publish --confirm --yes 實發並刪除（smoke Step 8）
- [ ] reply --confirm --yes 實發並刪除（smoke Step 9）
- [ ] publish-chain 實發 3 則 + 階梯式驗證 + 刪除（smoke Step 10）
- [ ] publish-chain 半途失敗報 posted_ids（Task 4 unit test）
- [ ] --on-failure=retry/rollback NotImplementedError（Task 4 + 8）
- [ ] --yes 無 --confirm exit 2（smoke Step 7）
- [ ] 非 TTY --confirm 無 --yes exit 2（smoke Step 6）
- [ ] Token 缺失 exit 1（smoke Step 5）
- [ ] CLAUDE.md 已更新（Task 10）
- [ ] SKILL.md 最小版已寫（Task 9）

- [ ] **Step 2: 最終回歸**

Run: `pytest`
Expected: 全綠。

- [ ] **Step 3: 檢查分支狀態**

Run:
```bash
git log --oneline main..HEAD
git status
```
Expected:
- 本次所有 commits 列出
- `git status` 乾淨

- [ ] **Step 4: 通知使用者 merge 準備**

告知：
- feat/cli-packaging 批次 A 全部完成
- 驗收 16 項全勾
- smoke test 紀錄在 handoff
- 建議 merge 路徑（squash / merge commit / rebase）
- 批次 B 留待下一 session

---

## Execution 要點

1. **每個 Task 獨立 commit**（已內嵌）
2. **TDD 紀律**：先寫 failing test、跑確認 fail、實作、跑確認 pass、commit
3. **既有測試永不壞**：每個 task 結束後跑 `pytest` 回歸
4. **檔案路徑以 repo root 為準**（`./x.py` 風格，不是 `threads_pipeline/x.py`）
5. **發文相關 test 100% mock**：絕不打真 API
6. **手動 smoke test 是唯一打真 API 的步驟**，做完立刻刪除測試貼文
7. **Token scope 前置檢查不可省略**（Task 11 Step 0）

---

## 完成後的下一步

- **批次 B**：另起 plan，實作 `posts search` / `posts list` / `post insights` / `post replies` / `account info` / `account insights` / `post delete`
- **E-重**：E-輕穩定後評估（從 advisor plan 吃、自動重試、排程…）
- **加入 Hub**：Advanced Access 核准 + 決定公開後，發 registry PR
