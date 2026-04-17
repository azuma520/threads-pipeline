# 批次 B2 Smoke 驗證紀錄（2026-04-17）

## 範圍

7 個新指令：
- 唯讀 6：`posts search` / `posts list` / `post insights` / `post replies` / `account info` / `account insights`
- 破壞性 1：`post delete`（四層安全 + 本地備份）

## 自動化測試結果

- **Unit + CliRunner**：169 tests 全綠
- **Subprocess 黑箱**：28 cases 全綠（B1 既有 15 + B2 新增 13）

## Commit 摘要（feat/cli-batch-b2，共 15 commits）

| Commit | 內容 |
|--------|------|
| `6eec863` | .gitignore 加 .deleted_posts/ |
| `7cca6d1` + `4ba8df3` | JSON envelope helpers（output.py） |
| `cf20162` + `6e84cd9` | 6 個唯讀 API helper（threads_client.py） |
| `923a904` | account info 指令 |
| `a093726` | account insights 指令 |
| `2f89886` | posts list 指令（--cursor 分頁） |
| `489faba` | post insights 指令 + _map_request_error |
| `d470c99` | posts search 指令（CJK 警告） |
| `c0f7256` | post replies 指令 |
| `7773c4f` | _backup.py 模組 |
| `60935e8` | delete_post core helper |
| `8b7ee7d` + `2782785` | post delete 指令（四層安全 + 備份） |

## 手動 smoke 結果

### 唯讀 6 指令（每個指令 human + --json）

- [x] `threads account info` / `threads account info --json`
- [x] `threads account insights` / `threads account insights --json`
- [x] `threads posts list --limit 3` / `threads posts list --limit 3 --json`
- [x] `threads posts list --cursor <cursor>` 翻頁驗證（若有 next_cursor）
- [x] `threads posts search "AI" --limit 3` / `threads posts search "AI" --json`
- [x] `threads posts search "人工智慧" --json`（CJK warning: EMPTY_RESULT_CJK）
- [x] `threads post insights 17952165552108332` / `--json`
- [x] `threads post replies 17952165552108332 --limit 3` / `--json`

### delete 真跑

- [x] 發布測試貼文：`threads post publish "B2 smoke 測試稿（待刪）" --confirm --yes`
  - post_id: 18390799444152846
- [x] Dry-run：`threads post delete 18390799444152846`
  - 結果：`[DRY RUN]`、exit 0、`.deleted_posts/` 無新增檔案
- [x] Dry-run JSON：`threads post delete 18390799444152846 --json`
  - 結果：envelope `{"ok": true, "data": {"dry_run": true, "post_id": "18390799444152846", ...}}`
- [x] 真刪：`threads post delete 18390799444152846 --confirm --yes`
  - 結果：`[OK] Deleted post 18390799444152846`、`[WARN] irreversible`、`.deleted_posts/18390799444152846_20260417-064655.json` 有新檔
- [x] 驗備份：`captured_before_delete: True, post_id: 18390799444152846, text: B2 smoke 測試稿（待刪）`

## Smoke 期間修正

1. **`follower_demographics` metric 移除**：`fetch_account_insights_cli` 原含 `follower_demographics` metric，Standard Access 下 API 回 400。移除後與 pipeline 版本一致（`views,likes,replies,reposts,quotes,followers_count`）。
2. **account insights human mode 修正**：API 回傳格式不一致——`views` 用 `values[0].value`、其他 metric 用 `total_value.value`。加入 `total_value` fallback 讓 human mode 正確顯示所有 metric。

## 已知問題 / 差距

1. **TOKEN_MISSING 在 --json 模式不吐 envelope**：B1 遺留的 `require_token()` 只走 stderr + exit 1。已在 plan Self-Review 明文 scope out 到 B3。
2. **INVALID_ARGS（Typer 框架層）在 --json 模式不吐 envelope**：框架限制，同 scope out 到 B3。
3. **pyright `reportPossiblyUnbound` 警告**：`error_with_code` 的 `NoReturn` 標註正確，但此版 pyright 不認 pyrightconfig 的 `reportPossiblyUnbound` key（需改為 `reportPossiblyUnboundVariable`）。不影響 runtime。
4. **Windows console 中文編碼**：`post replies` human mode 在非 UTF-8 console 下顯示亂碼，`--json` 模式正常。屬 Windows 終端限制，非 CLI bug。

## Codex 第三方審查

Plan 經 codex tech-spec-reviewer 審查（2026-04-17），判定「需小修」，修正項目全數完成：
- M1：`_search_keyword` signature 修正（`sort_order` 取代不存在的 `search_type`）
- M2：檔中間 import 改為檔頭（Task 7 / 12 的 Step 3a）
- M3：`_clamp_limit` docstring 加副作用說明 + test 補 stderr 驗證
- S1：Self-Review 加「已知差距」段落
- S2：`_backup.py` 移除 dead code（`except PermissionError`）
- S3：黑箱測試強化（delete dry-run --json + 3 個 missing-arg exit 2）
- S5：test assert 收緊為 `kwargs["cursor"]`

## 待使用者授權

- [x] 手動 smoke 全部打勾後 push 分支
- [ ] 使用者授權 merge 到 main
