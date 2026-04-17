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

- [ ] `threads account info` / `threads account info --json`
- [ ] `threads account insights` / `threads account insights --json`
- [ ] `threads posts list --limit 5` / `threads posts list --limit 5 --json`
- [ ] `threads posts list --cursor <cursor>` 翻頁驗證（若有 next_cursor）
- [ ] `threads posts search "AI" --limit 5` / `threads posts search "AI" --json`
- [ ] `threads posts search "人工智慧" --json`（CJK warning: EMPTY_RESULT_CJK）
- [ ] `threads post insights <real_post_id>` / `--json`
- [ ] `threads post replies <real_post_id> --limit 5` / `--json`

### delete 真跑

- [ ] 發布測試貼文：`threads post publish "B2 smoke 測試稿（待刪）" --confirm --yes`
  - post_id: _______________
- [ ] Dry-run：`threads post delete <id>`
  - 預期：`[DRY RUN]`、exit 0、`.deleted_posts/` 無新增檔案
- [ ] Dry-run JSON：`threads post delete <id> --json`
  - 預期：envelope `{"ok": true, "data": {"dry_run": true, ...}}`
- [ ] 真刪：`threads post delete <id> --confirm --yes`
  - 預期：`[OK] Deleted`、stderr `[WARN] irreversible`、`.deleted_posts/{id}_{ts}.json` 有新檔
- [ ] 驗備份：`cat .deleted_posts/<id>_*.json | python -c "import json,sys; d=json.load(sys.stdin); print(d['captured_before_delete'], d['post']['id'])"`
  - 預期：`True <post_id>`

## 已知問題 / 差距

1. **TOKEN_MISSING 在 --json 模式不吐 envelope**：B1 遺留的 `require_token()` 只走 stderr + exit 1。已在 plan Self-Review 明文 scope out 到 B3。
2. **INVALID_ARGS（Typer 框架層）在 --json 模式不吐 envelope**：框架限制，同 scope out 到 B3。
3. **pyright `reportPossiblyUnbound` 警告**：`error_with_code` 的 `NoReturn` 標註正確，但此版 pyright 不認 pyrightconfig 的 `reportPossiblyUnbound` key（需改為 `reportPossiblyUnboundVariable`）。不影響 runtime。

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

- [ ] 手動 smoke 全部打勾後 push 分支
- [ ] 使用者授權 merge 到 main
