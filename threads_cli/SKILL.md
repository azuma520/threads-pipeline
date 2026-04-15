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
