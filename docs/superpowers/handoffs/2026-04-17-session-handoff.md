# Session Handoff（2026-04-17）

## 本次完成事項

### 1. B2 Manual Smoke 驗證 + Merge

- 6 個唯讀指令（human + --json）全部通過
- delete 完整流程通過（publish → dry-run → dry-run --json → 真刪 → 備份驗證）
- Smoke 期間修了 2 個問題：
  - `follower_demographics` metric 在 Standard Access 下回 400，移除（`afb62a2`）
  - account insights human mode 缺 `total_value` fallback，補上（`afb62a2`）
- Merge `feat/cli-batch-b2` → main，push（`52456be`）

### 2. threads-cli Skill

- 建立 `skills/threads-cli/SKILL.md`（`73c0532`）
- 涵蓋 `threads` CLI 全部指令 + `threads-advisor` 交叉引用
- 包含決策表（什麼時候用哪個工具）和 8 個常見工作流
- 用 skill-creator 跑 eval：3 test cases × 2 iterations，with-skill vs baseline
  - Eval 1（找最佳文）：4 calls vs 18 calls（4.5x 效率差）
  - Eval 2（發文）：4 calls vs 5 calls（持平）
  - Eval 3（刪文）：4 calls vs 7 calls（持平）
  - v2 改善：Eval 1 with-skill 首選 `threads-advisor analyze` 快速路徑
- CLAUDE.md 更新 Available Skills 區塊

### 3. B3 收尾

修掉 B2 三個已知差距（`4b99c6e`）：
- `require_token()` 加 `json_mode` 參數，缺 token 時吐 JSON envelope（9 個 call site 更新）
- `cli.py` UsageError catch 在 `--json` 模式吐 `INVALID_ARGS` envelope
- `pyrightconfig.json` 修正 `reportPossiblyUnbound` → `reportPossiblyUnboundVariable`
- 新增 4 個 TOKEN_MISSING 測試，173 tests 全綠

### 4. CLI 開發指南

- `docs/dev/cli-development-guide.md`（`2080cf2`）
- 從 B1→B2→B3 經驗整理：架構、代碼模式、測試策略、Plan 撰寫、Skill 檔案
- 適用於下次用 Agent 開發 CLI 工具時參考

## 當前狀態

- **分支**：main，已 push
- **Tests**：173 全綠（169 B2 + 4 B3 新增）
- **CLI 指令數**：10 個（3 寫入 + 7 唯讀/刪除）
- **Skill**：`skills/threads-cli/SKILL.md`，已 commit

## Commit 摘要

| Commit | 內容 |
|--------|------|
| `afb62a2` | account insights smoke 修正（follower_demographics + total_value） |
| `52456be` | Merge feat/cli-batch-b2 → main |
| `73c0532` | threads-cli skill + CLAUDE.md 更新 |
| `4b99c6e` | B3 收尾（TOKEN_MISSING / INVALID_ARGS envelope + pyright config） |
| `2080cf2` | CLI 開發指南 |

## 未完成 / 下一步可考慮

- **Advanced Access 審核**：仍在等待，核准後 `posts search` 才能跨帳號 + 中文搜尋
- **開始實際使用**：工具到位，可用 `threads-advisor analyze` 看數據、`review` 審草稿、CLI 發文
- **其他功能**：排程發文、自動回覆、insights 定期追蹤報告等
