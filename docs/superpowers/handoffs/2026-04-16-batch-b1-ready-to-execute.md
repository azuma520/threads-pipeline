# Handoff：批次 B1 Ready to Execute

**日期**：2026-04-16
**狀態**：Spec approved、Plan 寫完、等下個 session 執行

## TL;DR

- **Spec**：`docs/superpowers/specs/2026-04-16-cli-batch-b-design.md`（含批次 B 全範圍、已被 tech-spec-reviewer 審過 + 修正）
- **Plan**：`docs/superpowers/plans/2026-04-16-cli-batch-b1.md`（B1 段 8 個 task，含完整 code、test、command、commit）
- **分支策略**：B1 走 `feat/cli-batch-b1`，merge 後再開 B2（B2 plan 未寫，等 B1 完成後根據實際情況寫）

## 今天 session 完成的事

1. 五個角度（A/C/D/B/E）討論 CLI vs App 的產品思維，最終產出：
   - `docs/dev/private/product-thinking.md`（私人備忘錄，.gitignore）
   - 記憶：`project_product_boundary.md`（Threads 能做的不重做原則）
2. Brainstorming：批次 B 四個開放議題逐題拍板
3. Spec 寫完、self-review、tech-spec-reviewer 審查、採納修正
4. Plan 寫完並 commit

## 四個議題的拍板（plan 已反映）

| 議題 | 決策 |
|---|---|
| `--json` flag | 全啟用（B2 實作 warnings envelope；B1 保留 inert） |
| 分頁策略 | 只抓第一頁 + `--cursor`（B2 才用到） |
| CLI 框架 | 同步遷移到 Typer（B1 做） |
| Delete 保護 | 警告 + `.deleted_posts/` 本地備份（B2 做） |

## 下個 session 的起手指令

```
我要執行批次 B1 plan。

先讀：
- docs/superpowers/plans/2026-04-16-cli-batch-b1.md（plan 本身）
- docs/superpowers/specs/2026-04-16-cli-batch-b-design.md（spec 參考）
- docs/dev/batch-a-lessons.md（批次 A 踩坑清單）
- docs/superpowers/handoffs/2026-04-16-batch-b1-ready-to-execute.md（本檔）

然後執行 plan 的 Task 1（開 feat/cli-batch-b1 分支 + 加 typer 依賴）。
用 subagent-driven-development 模式（每個 task 一個 fresh subagent +
task 之間 review checkpoint）。
```

## 執行模式建議

Plan 結尾提供兩種模式：

**1. Subagent-Driven（推薦）**
- 每個 task dispatch fresh subagent 執行
- Task 之間有 review checkpoint
- 適合 B1 這種「逐步驗證、不容錯」的遷移工作
- 啟用：`Skill: superpowers:subagent-driven-development`

**2. Inline Execution**
- 在同個 session 用 executing-plans skill 執行
- Batch 執行 + checkpoint review
- 適合 context 空間充足、想快速跑完的情境

建議選 **Subagent-Driven**——B1 有 8 task、規模比批次 A（12 task inline）稍小但每 task 風險更高（Typer 遷移每步可能出 Click 特有問題），fresh subagent + review 的保護比較穩。

## 需要使用者授權的 checkpoint

Plan 執行期間以下步驟必須經過使用者：

- [ ] Task 8 Step 6：`git push -u origin feat/cli-batch-b1` — 推分支
- [ ] Task 8 後：要不要 merge 到 main

其他 task（Task 1-7）的 commit 都在新分支，相對安全可以自動執行。

## 不要重新討論

- 四個議題的拍板決策（寫在 spec 裡）
- Typer 為框架（已拍板）
- B1 不做新指令（那是 B2）
- `publish-chain` rollback 不做（spec 明確 scope out）
- `reply` 為 top-level command（批次 A 行為保留）

## 可能遇到的陷阱（批次 A lessons 的教訓）

1. **`pip install -e` 可能升級 pytest**（1.2 lesson）→ 若 pytest-asyncio 爆，`pip install -U pytest-asyncio`
2. **CLI 啟動沒載 .env**（1.3 lesson）→ plan Task 3 的 cli.py 已含 `_load_dotenv()`
3. **setuptools `package-dir` build time 驗證目錄存在**（1.1 lesson）→ B1 不新增 package，僅改 module，應不觸發此問題

## 連結

- Spec：`docs/superpowers/specs/2026-04-16-cli-batch-b-design.md`
- Plan：`docs/superpowers/plans/2026-04-16-cli-batch-b1.md`
- 批次 A lessons：`docs/dev/batch-a-lessons.md`
- 批次 A smoke：`docs/superpowers/handoffs/2026-04-15-threads-cli-smoke.md`
- 批次 B kickoff（原始）：`docs/superpowers/handoffs/2026-04-15-batch-b-kickoff.md`
