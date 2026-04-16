# Handoff：批次 B1 Smoke 驗證

**日期**：2026-04-16
**分支**：`feat/cli-batch-b1`
**狀態**：Smoke dry-run 通過，未真發，等待使用者授權 push/merge

## 範圍

批次 B1 — Typer 遷移 + 既有指令行為回歸。共 8 task、10 個 commits（含 Task 8 cleanup + 本 handoff）。

## 關鍵里程碑

- Subprocess 黑箱測試 **15/15 綠**（跨 argparse→Typer 不變，regression 防線）
- Typer CliRunner 重寫單元測試 **8/8 綠**（Task 8 cleanup 移除 2 個 subprocess 重複後）
- 完整測試 suite **100/100 綠**（Task 8 A.4 移除 `test_threads_cli.py` 內 `test_threads_cli_version` / `test_threads_cli_help` 兩個與 `test_cli_blackbox.py` 的 `test_bbox_*` 重複的 subprocess 測試，canonical 位置統一到 blackbox 檔）
- 手動 dry-run **三個指令（publish / reply / publish-chain）全通過**
- 錯誤路徑 smoke（無 token）**exit 1 + [ERROR] to stderr**
- 批次 A lessons 1.2（pytest-asyncio）未觸發、1.3（.env 自動載入）已在 `cli.py:main()` 保留

## 未做的事

- **未真發文**：B1 是純遷移、沒新增 API 行為，smoke dry-run 已足夠；真發留給 B2 新指令一起做
- 批次 A smoke handoff 的所有步驟未逐字重跑（只跑了 B1 新測試層 + 手動 dry-run + 補充 error-path）

## 已知 tooling 限制（非阻塞）

- Pyright 在 Windows 上對 `sys.stdout.reconfigure` 的 TextIO 型別誤報；Task 8 cleanup 已加 `pyrightconfig.json`（`extraPaths: ["."]`）緩解大部分 import 解析問題，reconfigure 兩行留待日後加 `# type: ignore` 或改用 `typing.cast`
- Windows subprocess `isatty()` 回 True（POSIX 回 False）——`test_bbox_publish_confirm_without_yes_in_ci` 已用 branching assertion 同時涵蓋兩種平台
- Git Bash `printf` 經 stdin 傳中文給 subprocess 時會 mojibake（bytes/chars 計數也會混淆）；這是 shell 層級問題非 CLI bug，Python `subprocess.run(..., encoding="utf-8")` 路徑運作正常

## Commit 列表（`git log main..feat/cli-batch-b1 --oneline`）

```
f6883c4 style(cli): B1 cleanup — pyrightconfig + error() NoReturn + help 字串一致性
2959898 test(cli): 重寫 CLI 單元測試配合 Typer handler signature
bd9a284 feat(cli): 遷移 reply 指令到 Typer（top-level）
11ddbaa feat(cli): 遷移 post publish-chain 指令到 Typer
ca16a0e feat(cli): 遷移 post publish 指令到 Typer
025ff83 refactor(cli): 建立 Typer app 骨架 + subcommand group modules
8c2d915 style(cli): 移除 test_cli_blackbox.py 未使用的 pytest import
a8ba5d1 test(cli): 加入 subprocess 黑箱測試層作為 Typer 遷移的 regression 防線
9fcf4a9 chore(deps): 加入 typer 依賴（批次 B1 準備）
```

（本 handoff commit 會在上述列表之上。）

## 測試命令（結果）

```
$ python -m pytest -q
........................................................................ [ 72%]
............................                                             [100%]
100 passed in 4.18s
```

## 手動 smoke 命令與輸出

### B.1 `threads --version` / `threads --help`（entry point in PATH）

```
$ threads --version
threads 0.1.0

$ threads --help
Usage: threads [OPTIONS] COMMAND [ARGS]...
  Threads API operations CLI (CLI-Anything compatible)
Options:
  --version          Show version and exit
  --json             Output as JSON (B1: parsed; B2: 唯讀指令啟用完整 envelope)
  --help             Show this message and exit.
Commands:
  reply     Reply to an existing post.
  post      Single post operations
  posts     Posts list operations (batch B2)
  account   Account operations (batch B2)
```

- `threads post --help` → 列出 `publish` / `publish-chain`
- `threads posts --help` / `threads account --help` → 空 Typer group（B2 pending）
- `threads reply --help` → 顯示 `post_id` / `text` args + `--confirm` / `--yes`（Task 8 新補的 help 字串已顯示）

### B.2 Dry-run 三連發

```
$ threads post publish "這是測試訊息"
[DRY RUN] Would publish:
---------------------------------
這是測試訊息
---------------------------------
Character count: 6
Add --confirm to actually publish.
EXIT=0

$ threads reply FAKE_POST_ID "測試回覆"
[DRY RUN] Would reply to post FAKE_POST_ID:
---------------------------------
測試回覆
---------------------------------
Character count: 4
Add --confirm to actually reply.
EXIT=0

$ printf "第一則\n第二則\n" | threads post publish-chain -
[DRY RUN] Would publish chain of 2 posts:
---------------------------------
1/2 (opener):	... (7 chars)
2/2 (reply):	... (7 chars)
---------------------------------
Total: 2 posts, 14 chars
On-failure policy: stop
Add --confirm to actually publish.
EXIT=0
```

（publish-chain 中文內容在 Git Bash 下經 stdin 傳送會 mojibake，但 CLI 本身 exit 0，見上方「已知 tooling 限制」。）

### B.3 Error-path（無 THREADS_ACCESS_TOKEN，cwd 切到 tempdir 避開 .env）

```
$ THREADS_ACCESS_TOKEN="" threads post publish "x" --confirm --yes
[ERROR] THREADS_ACCESS_TOKEN not set.
  Add it to .env or export as environment variable.
  Get a token: https://developers.facebook.com/tools/access-token-tool/
EXIT=1
```

## 下一步

- 等待使用者授權：
  1. `git push -u origin feat/cli-batch-b1`
  2. 開 PR 或直接 merge 到 main
- B2 plan 尚未寫，B1 merge 後再根據實際情況寫
