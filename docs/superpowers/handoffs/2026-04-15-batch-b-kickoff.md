# Handoff：批次 B Kick-off

**日期**：2026-04-15（批次 A merge 當天）
**狀態**：批次 A 結案、批次 B 未開始

## 給下個 session 的 TL;DR

批次 A 已 merge 到 main 並 push（commit `2ef36ba`）。下個 session 要做批次 B。

**第一步必讀（省 1-2 小時除錯）**：`docs/dev/batch-a-lessons.md`

那份有：
- 批次 A 踩過的 3 個 plan 漏洞（批次 B 會重現的，提早避開）
- Threads API 實測 gotcha（race condition / DELETE scope）
- CLI 設計模式（dispatch table、四層安全、exit code 約定）
- 批次 B 專屬 checklist 和開工提醒

## 批次 B 範圍

依原 spec（`docs/superpowers/specs/2026-04-15-threads-cli-packaging-design.md`）：

| 指令 | 類型 | 備註 |
|---|---|---|
| `threads posts search <keyword>` | 唯讀 | 中文搜尋回 0 筆是已知限制 |
| `threads posts list` | 唯讀 | 列自己最近貼文、可能要分頁 |
| `threads post insights <id>` | 唯讀 | 單篇數據 |
| `threads post replies <id>` | 唯讀 | 列回覆 |
| `threads account info` | 唯讀 | 帳號基本資料 |
| `threads account insights` | 唯讀 | 帳號數據，可能和 insights_tracker.py 重疊 |
| `threads post delete <id>` | 寫入 | 破壞性，套四層安全 |

## 建議工作流（已驗證可用）

1. **先讀** `docs/dev/batch-a-lessons.md`（section 6 批次 B checklist）
2. **寫 plan**（仿 v1.1 結構、每 task 獨立 commit、TDD pattern）
3. **雙審查**（spec reviewer + plan reviewer）— 批次 A 的 P0 建議採納率 100%，不要省
4. **新分支** `feat/cli-batch-b`（**不**在 main 直接做）
5. **inline 執行**（12 task 內 inline 比 subagent-driven 快）
6. **Smoke test** — 零副作用那批先跑，寫入 / delete 指令**要先授權**

## 批次 B 的開放議題（plan 撰寫時要決）

- **`--json` flag 啟用**：批次 A 是 inert，批次 B 唯讀指令該實作
- **分頁策略**：`list` / `replies` Threads API 有 cursor pagination，要不要 CLI 層自動翻頁或傳 cursor 給使用者
- **argparse vs click/Typer**：指令數變 ~10+ 時可重議（lessons doc section 6.3 有評估要點）
- **delete 的 undo 設計**：Threads API 的 delete 是**不可逆**的，plan 要決定是否多一個「30 秒內後悔視窗」之類的保護

## 不要重新討論

批次 A 已拍板這些（見 lessons doc section 6.3）：
- 扁平 layout（**不**改 src/ layout）
- publisher.py 在 repo root
- ASCII 前綴（`[ERROR]` / `[OK]`）
- `--confirm --yes` 雙旗標
- exit code 約定（0/1/2）

## 起手指令

新 session 可以直接貼：

```
我要做批次 B（list / insights / replies / account / delete）。
先讀 docs/dev/batch-a-lessons.md 和
docs/superpowers/handoffs/2026-04-15-batch-b-kickoff.md，
然後幫我寫批次 B 的 plan。
```
