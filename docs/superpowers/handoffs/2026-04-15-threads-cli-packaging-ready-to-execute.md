# Handoff：Threads CLI Packaging — Ready to Execute

**日期**：2026-04-15
**分支**：`feat/cli-packaging`
**狀態**：Brainstorming + Design + Plan 全部完成、雙審查通過，準備進執行階段

---

## 給下個 session 的 TL;DR

使用者想把 `threads_pipeline` 打包成 CLI 工具。**所有設計文件都已寫完、審過、commit**。下個 session 開啟後：

1. 切到 `feat/cli-packaging` 分支
2. 讀 `docs/superpowers/plans/2026-04-15-threads-cli-packaging.md`（v1.1，2116 行，12 個 task）
3. 跟使用者確認「執行方式」後開工（Subagent-Driven 推薦 / Inline Execution）

**不要重新 brainstorm、不要重新 review。設計階段已結案。**

---

## 為什麼換 session

Context 快爆。這一 session 包含：
- cli-anything 生態研究教學（使用者從零學打包概念）
- 6 段 design section 逐段確認
- 兩輪雙 reviewer agent 審查（spec 一次、plan 一次）
- 兩次完整文件修訂

新 session 只需要讀完成的 spec + plan，context 瞬間降低。

---

## 已完成的交付物

全部在 `feat/cli-packaging` 分支：

| Commit | 檔案 | 內容 |
|---|---|---|
| `e3ea70a` | `docs/dev/cli-anything-research.md` | CLI-Anything 研究筆記（術語字典 + 4 個 Step） |
| `a8863ef` | 同上（追加） | 未來 roadmap（ruff / E-重 / Hub 加入） |
| `05479df` | `docs/superpowers/specs/2026-04-15-threads-cli-packaging-design.md` | Spec v1.0（初版） |
| `dc03ab4` | 同上（追加） | 加入 publish-chain 到 Level 1 |
| `8a65cc4` | 同上（v1.1） | Spec v1.1：雙審查後修訂 |
| `45e1ff8` | `docs/superpowers/plans/2026-04-15-threads-cli-packaging.md` | Plan v1.0（初版，12 task） |
| `99a59a1` | 同上（v1.1） | Plan v1.1：雙審查後修訂 |

**下個 session 唯一要讀的**：spec v1.1（`8a65cc4` 之後的版本）+ plan v1.1（`99a59a1` 版本）。

---

## 關鍵設計決策（不要再改）

使用者已經明確拍板，重複討論會浪費 context：

### 範圍
- **E-輕**：包裝既有 code 為 CLI，不加新功能
- **批次 A**：advisor（零改）+ publish / reply / publish-chain
- **批次 B**：list / insights / replies / account / delete（另起 plan，下個 session 不做）

### 技術選擇
- **保留 argparse**（不換 click/Typer）
- **pyproject.toml**（不用 setup.py）
- **扁平 layout**（repo root 就是 package）
- **publisher.py 放 repo root**（跟 threads_client.py 同層，不在 threads_cli/ 裡）
- **三個 entry points**：`threads-advisor` / `threads` / `cli-anything-threads`（保留 Hub 別名）

### 安全設計
- 寫入指令預設 dry-run
- `--confirm` + `--yes` 才 Agent 模式
- `--yes` 無 `--confirm` → exit 2（hard-error，非靜默 dry-run）
- 非 TTY + `--confirm` 無 `--yes` → exit 2
- `publish-chain` 半途失敗策略 `stop`（`retry` / `rollback` 保留 flag 但 raise NotImplementedError）

### 刻意排除
- Session / undo / REPL
- AI 內容審查
- 串文自動重試 / rollback（Level 1）
- 自動化 E2E（避免垃圾發文）
- 發佈 PyPI
- 改 argparse 到 click / Typer

---

## 執行前必讀的陷阱（審查揪出、plan 已修）

這些是 plan 修訂 v1.1 已經處理的問題，執行時**照 plan 做就不會踩**：

1. **檔案路徑**：`./publisher.py` 在 **repo root**（不是 `threads_pipeline/publisher.py`）。扁平 layout，Python import 路徑 ≠ 檔案系統路徑
2. **pyproject.toml packages**：用明示 list，不用 `find`（避免 tests/ 等誤包）
3. **Windows UTF-8**：用 `sys.stdout.reconfigure(...)`，**不要**用 `os.environ.setdefault("PYTHONUTF8", "1")`（runtime 無效）
4. **argparse dispatch**：`reply` 沒有 `.action` 屬性，用 `getattr(args, "action", None)`
5. **publish_chain opener fail**：第 1 則失敗拋 plain `PublishError`，不升級為 `ChainMidwayError`（語義）
6. **ChainMidwayError catch 順序**：subclass 在前 → PublishError 在後，否則被吞掉
7. **ASCII prefix**：`[ERROR]` / `[OK]` / `[WARN]`，不用 `✗` / `✓` / `⚠`（cp950 safe）
8. **Token scope**：smoke test 前先驗證 token 有 `threads_content_publish` 權限

---

## 下個 session 怎麼開場

### 選項 A（推薦）：直接進執行

在新 session 中貼這段給 Claude：

```
我要執行 docs/superpowers/plans/2026-04-15-threads-cli-packaging.md（v1.1）
分支已在 feat/cli-packaging。
設計階段已結案，不重新討論。
用 Subagent-Driven（每個 task 一個 fresh subagent + 你審查 + 我審查）。
開始 Task 0。
```

### 選項 B：先對齊再開工

如果想再確認一下共識：

```
切到 feat/cli-packaging 分支。
讀 docs/superpowers/handoffs/2026-04-15-threads-cli-packaging-ready-to-execute.md
簡述你對「現在該做什麼」的理解後等我確認。
```

---

## 重要：使用者特性備忘

（幫助新 session 的 Claude 維持溝通風格）

- **使用者是程式新手**，自稱「程式小白，只有基本觀念沒有經驗」
- 使用者偏好**繁體中文**溝通
- 使用者會**主動要求第三方審查**（spec / plan 都審過了，執行階段可能也會要求審查 code）
- 使用者**重視理解**：執行階段若有決策點，講清楚 why 再做
- 使用者**強調版控紀律**：明確要求開發前先開新分支（已做）
- 使用者**有經營 Threads 帳號**（azuma520 / azuma01130626），實發測試請務必 **手動刪除**乾淨

---

## 目前分支狀態（給 git 接手用）

```
99a59a1 docs(plan): v1.1 審查後完整修訂                            ← HEAD
45e1ff8 docs(plan): threads CLI 批次 A 實作 plan（v1.0）
8a65cc4 docs(spec): v1.1 審查後修訂 — P0/P1/P2 全數採納
dc03ab4 docs(spec): 加入 publish-chain 到 Level 1 批次 A
05479df docs(spec): threads CLI 化 Level 1 + E-輕 design spec
a8863ef docs(research): 補未來 roadmap
e3ea70a docs(research): CLI-Anything 研究筆記
8d3946c ← main 基礎
```

`git status` 應該是乾淨的（只有這個 handoff 檔是未 track 的）。

---

## Task List（給 TaskCreate 參考）

下個 session 開始時建議建立的 task list：

1. [pending] Read spec v1.1 and plan v1.1
2. [pending] Confirm execution mode with user (Subagent-Driven vs Inline)
3. [pending] Task 0: pyproject.toml + pip install 驗證
4. [pending] Task 1: threads_cli 骨架 + dispatch table
5. [pending] Task 2: publisher.publish_text
6. [pending] Task 3: publisher.reply_to
7. [pending] Task 4: publisher.publish_chain
8. [pending] Task 5: safety 層
9. [pending] Task 6: CLI post publish
10. [pending] Task 7: CLI reply
11. [pending] Task 8: CLI post publish-chain
12. [pending] Task 9: SKILL.md
13. [pending] Task 10: CLAUDE.md 更新
14. [pending] Task 11: 手動 smoke test（實發 + 刪除）
15. [pending] Task 12: 驗收 checklist

---

## 結束語

這個 session 完成了從「使用者問『可以包成 CLI 嗎』」到「完整可執行的 plan」的全部設計工作。下個 session 的任務純粹是執行 — 照 plan 做、跑測試、實發一次、刪除、merge。

**如果下個 session 的 Claude 想重新討論任何設計決策，請先讀這份 handoff 和 spec/plan**。所有 why 都有文件化，不要再跟使用者重複討論已經拍板的事。
