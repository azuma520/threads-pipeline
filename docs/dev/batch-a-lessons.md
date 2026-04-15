# 批次 A 開發經驗筆記

**紀錄日期**：2026-04-15（批次 A merge 當天）
**涵蓋範圍**：threads CLI packaging 從 design → execute → smoke → merge

## 為什麼寫這份

1. **批次 B 開發前必讀**：批次 A 踩過的坑 80% 會在批次 B 重現（相同 layout、相同 API、相同工作流）。讀一次能省至少 1-2 小時的重複除錯。
2. **未來功能延伸的參考**：E-重（advisor plan 吃 publish-chain）、批次 C（Hub 加入 / PyPI 發佈）等新功能，很多決策的 why 在這裡。
3. **第三方審查哪些建議「在實戰真的派上用場」**：spec/plan reviewer 提了 20+ 條，實際執行證實哪些是 P0 關鍵、哪些是 P2 可選；未來類似專案知道該花精力在哪。

## 如何使用

- 批次 B 開始前：掃一次「給批次 B 的具體建議」段（最末）
- 遇到問題查閱：`Ctrl-F` 搜「問題」找最接近的 case
- 不是教科書，只記**非顯而易見、重複發生、下次會忘**的東西

---

## 1. Plan vs Reality 踩坑（plan 漏寫、執行才暴露）

### 1.1 setuptools `package-dir` 在 build time 驗證目錄存在

**情境**：Task 0 pyproject.toml 建好後跑 `pip install -e ".[dev]"`。
**Plan 預測**：「threads_cli/ 還不存在，editable install 會抱怨但不 fail（entry_point lazy 驗證）」。
**實際**：setuptools build 階段就 raise `error: package directory 'threads_cli' does not exist`，install **fail**。
**解法**：Task 0 提前建 `threads_cli/__init__.py` 空 stub（Task 1 本來就要建，提前不虧）。
**為何記**：下次用扁平 layout + 多 package 配置的新專案，第一次 install 一定碰到，知道要先建空 dir 就不卡。
**批次 B 怎麼用**：不影響（批次 B 不動 packaging）。

### 1.2 pip install 可能升級 pytest 破壞 pytest-asyncio

**情境**：`pip install -e ".[dev]"` 把 pytest 從 7.4 升到 9.0，pytest-asyncio 0.23.2 不相容（`AttributeError: 'Package' object has no attribute 'obj'`），全 test collection fail。
**解法**：`pip install -U pytest-asyncio`（升到 1.3.0 就相容）。
**為何記**：pytest 版本是依賴鏈裡易動搖的一環。未來 dev 環境重建、CI 第一次跑、都可能重現。**不要盲目 downgrade pytest**——往新版走、同步升插件。
**批次 B 怎麼用**：若 CI 或新機器 setup 碰到同錯，直接升 plugin。

### 1.3 CLI 啟動需自載 `.env`，Python 不會自動做

**情境**：Smoke test 跑 `threads post publish "..."` 全部回「Token not set」，即使 `.env` 存在、`THREADS_ACCESS_TOKEN` 也寫在裡面。
**原因**：Python **不會**自動讀 `.env`（除非用 python-dotenv）。本專案 `main.py` 有 `_load_dotenv()`，`advisor.main()` 會呼叫它，但新加的 `threads_cli/cli.py` 的 `main()` 沒呼叫——**plan 寫時忘了**。
**解法**：cli.py 的 `main()` 開頭 try-import + 呼叫 `_load_dotenv()`，用 try/except 包（允許外部 env 優先）。
**為何記**：這是**新增 CLI entry point 時必做的最小 bootstrap**，很容易漏。批次 B 加新 entry point（例如 `threads-insights-daily` 之類）會重現。
**批次 B 怎麼用**：任何新 entry point 的 `main()` 第一步永遠是 `_load_dotenv()`。寫進 checklist。

---

## 2. Threads API 實測發現（光看文件看不到）

### 2.1 Race condition：剛發完的 post 立刻當 reply_to 會 400

**情境**：`publish_chain` 第一次實跑就碰到：第 1 則 publish 成功（拿到 post_id）→ 立刻用它當第 2 則的 reply_to → 第 2 則 Step 2 publish 回 `API 400: The requested resource does not exist`。
**推測原因**：Threads API 內部索引異步建置，post_id 回傳時資料還沒 commit 完成。第 2 次執行同樣的 chain 就成功了。
**目前處理**：Level 1 明確不實作 retry（on_failure=stop）。`ChainMidwayError` 正確拋出、含已發 ID、使用者可手動重試。
**為何記**：
1. 這是**靠 mock test 絕對測不到**的真實行為——不記下來未來會忘、會被問「為什麼有時失敗」。
2. **ChainMidwayError 的設計在真實條件下被驗證有效**——之前審查時有人質疑「是不是過度設計」，實戰證明不是。
**批次 B 怎麼用**：批次 B 不實作 retry（符合 Level 1 邊界）；但**若未來做 E-重的 auto-retry**，已知需要在 chain 節點間加 **≥2 秒 sleep** 或 poll 直到 post_id 可讀。

### 2.2 DELETE API 在 `threads_content_publish` scope 下可用

**情境**：Smoke test 發完測試貼文需要刪除，本來擔心 scope 不足要登網頁手刪。
**實測**：`DELETE /v1.0/{post_id}?access_token=...` 回 `{"success":true,"deleted_id":"..."}`，**不需要額外 scope**。
**為何記**：批次 B 的 `threads post delete` 指令**技術上可行**。審查時 reviewer 曾猶豫是否 Level 1 就要做，後來排到批次 B；現在知道 API 端沒問題，批次 B 可放心實作。
**批次 B 怎麼用**：`threads post delete <post_id>` 直接包 DELETE API，加同樣的 `--confirm --yes` 安全層即可。

### 2.3 串文 UI 顯示：Threads 真的有階梯式層級

**情境**：擔心 Threads UI 會把所有 reply 扁平化顯示（flat），讓「第 3 則 reply 到第 2 則」和「第 3 則 reply 到第 1 則」看起來一樣。
**實測**：Threads web UI **正確顯示巢狀階梯**——第 3 則明顯在第 2 則下方縮排，不是平行於第 2 則。
**為何記**：這影響「階梯式 vs flat」的設計辯論結果。未來若使用者問「為什麼不全部 reply 到 opener」，答案是「Threads UI 呈現會不一樣、階梯式更像『討論串』」。

---

## 3. 第三方審查建議哪些「真的派上用場」

審查提了 20+ 條，實戰分類：

### P0（沒做會出 bug）— 4 條全中

| 建議 | 實戰狀況 |
|---|---|
| `_post()` body['error'] 加 isinstance 防禦 | 未實測觸發，但**未來必碰**（Meta API 歷史上 error 欄位型態變過） |
| `publish_chain` opener failure 拋 plain `PublishError`（不升級 Midway） | CLI 層 catch 語義正確，reviewer 的擔心是對的 |
| `ChainMidwayError` catch 順序（subclass 在前） | CLI Task 8 實作時差點寫反，幸好 plan 已加註解 |
| Token scope 前置檢查（`threads_content_publish`） | Smoke step 0 做 GET /me 驗證，省掉「為什麼 publish 會 400」的除錯時間 |

**結論**：**P0 建議採納率 100%，沒有一條是過度防禦**。未來類似專案的 reviewer，P0 標籤可以默認採納。

### P1（做了比較穩）— 3/4 有用

| 建議 | 實戰狀況 |
|---|---|
| 明示 `packages` list 不用 `find` | 避免 `tests/` 被當 package 誤包 — 有用 |
| argparse dispatch key `getattr(args, "action", None)` | `reply` 無 subparser 沒 `action` 屬性，會 AttributeError — 救到 |
| ASCII `[ERROR]`/`[OK]` 前綴取代 `✗`/`✓` | Windows cp950 終端印 `✗` 會亂碼 — 小 UX 改善 |
| Windows UTF-8 用 `sys.stdout.reconfigure` 不用 `os.environ.setdefault("PYTHONUTF8")` | `setdefault` 在 runtime 無效，reviewer 是對的 |

### P2（測試精度）— 有邊際價值

| 建議 | 實戰狀況 |
|---|---|
| publish_chain 500 字元邊界測試 | 加了，沒實際救到 bug，但提高信心 |
| `--on-failure=retry` 用 `== 2` 而非 `in (1,2)` | 精確匹配，抓到 NotImplementedError 的 exit code 策略 |

**總結**：**第三方審查 ROI 極高**。雙 reviewer（spec reviewer + plan reviewer）提的建議大部分都在實戰出現。**未來批次 B / 新大型功能一定要再做審查**，不要省這一步。

---

## 4. TDD / 工作流結論

### 4.1 12 task inline 執行比 subagent-driven 快

**情境**：原 plan 推薦 subagent-driven（每 task 派 fresh subagent）。實際選 inline，12 task 一氣呵成。
**結果**：
- Inline 全程約 **~20 min active time**（不含 smoke）
- Subagent-driven 估計會多 **30-50% overhead**（每 task context 切換、重讀 plan）
**判斷依據**：
- Plan 夠詳細（步驟、code、test 都已寫在 plan 裡），新 subagent 讀 plan 即可執行，但 inline 的 Claude 剛做完前一 task 記憶猶新，**更快**
- 12 task 程式碼總量 ~600 行，context 遠未爆
**批次 B 怎麼用**：若批次 B 結構類似（線性依賴、每 task 可重複的 pattern），**繼續用 inline**。若是多個平行獨立任務，才考慮 subagent-parallel。

### 4.2 TDD 的失敗測試那步真的救到東西

**情境**：每個 task 先寫 test、看它 fail、再實作、看它 pass。**過程中抓到**：
- Task 4 test 一開始沒寫 opener fail 的 plain-PublishError 斷言，補上後才發現 early implementation 把 opener fail 也升級成 ChainMidwayError
- Task 6 cli dispatch mock 路徑寫錯，fail 階段就看到 `AttributeError: 'module' has no attribute 'publish_text'`，10 秒內修

**批次 B 怎麼用**：**絕對不要**省略「跑一次 test 確認 fail」那步。那步是免費的 sanity check，不做會在實作階段吃大 debug 時間。

### 4.3 每 task 獨立 commit 的價值

**情境**：14 個 commits 每個都獨立可 review / rollback。
**實戰價值**：
- Task 6 寫到一半發現 import 組織不好，想 revert 只回 Task 6 這一個 commit，其他 task 不動
- Smoke 階段發現 dotenv 漏洞，獨立一個 `fix:` commit，不污染 feature commit 的訊息

**結論**：commit 粒度細，merge commit 訊息再把 high-level 綜合起來，兩全其美。**未來大 PR 繼續這樣做**。

---

## 5. CLI 設計模式（可複用）

### 5.1 Dispatch Table 優於 if-elif

```python
COMMANDS = {}
def _register(key): ...  # decorator

@_register("post.publish")
def cmd_post_publish(args): ...
```

**優勢**：
- 新增指令不用改 main flow
- Test 可 `from cli import COMMANDS` 檢查註冊完整性
- 未來遷移 click/Typer 時結構對齊

**批次 B 怎麼用**：**所有新指令都註冊到同一個 COMMANDS**，不要另開 branch。

### 5.2 四層安全（寫入指令）

1. **Token 檢查**（`require_token()`）— 缺則 exit 1
2. **預設 dry-run** — 不帶 flag 只印，不執行
3. **TTY 互動確認** — `--confirm` 但沒 `--yes` 時進 `input()` y/N
4. **Agent 模式** — `--confirm --yes` 雙 flag 才跳過互動

**關鍵規則**：
- `--yes` **無** `--confirm` → hard-error exit 2（不是「靜默 dry-run」，使用者意圖明確就 fail-fast）
- 非 TTY **有** `--confirm` **無** `--yes` → hard-error exit 2（CI 下互動會 hang）

**批次 B 怎麼用**：批次 B 的 `delete` 指令**完全複用**這四層；`insights` 等唯讀指令**不需要**這四層（沒 side effect）。

### 5.3 錯誤 exit code 約定

| Code | 情境 |
|---|---|
| 0 | 成功 / dry-run / 使用者取消 |
| 1 | API 失敗、網路、Token、檔案、業務邏輯 error（如 ChainMidwayError） |
| 2 | 使用者用法錯誤、NotImplementedError、unknown subcommand |

**批次 B 怎麼用**：延續此約定，**不新增 code**（3/4/5... 沒必要）。

---

## 6. 給批次 B 的具體建議（開工前掃一次）

### 6.1 Checklist（新 plan 撰寫時必含）

- [ ] 新增的 CLI entry point `main()` **第一步呼叫 `_load_dotenv()`**（踩坑 1.3）
- [ ] 新增寫入指令**繼承四層安全**（section 5.2）
- [ ] 新增唯讀指令**實作 `--json` flag**（批次 A 是 inert 的，批次 B 該啟用）
- [ ] 新 package 目錄在 `pyproject.toml` `packages` list 明示加入
- [ ] 任何 API call 的 `body['error']` 解析加 `isinstance(err, dict)` 防禦
- [ ] Test 用 mock（`patch("threads_pipeline.publisher.requests.post", ...)`），**絕不打真 API**
- [ ] 至少一次手動 smoke test（含實發 + DELETE 清理）
- [ ] 分支隔離：**新分支**（`feat/cli-batch-b` 之類），不在 main 直接做

### 6.2 批次 B 預估範圍提醒

Plan 列的批次 B = list / insights / replies / account / delete。但注意：
- **delete** 是寫入（破壞性）— 套四層安全 + **加 undo 提示**（`[INFO] Deleted {id}. To undo: this is irreversible on Threads.`）
- **list / replies** 可能要分頁（Threads API pagination），先查 spec
- **insights** 是唯讀但資料量大，考慮 `--json` + `--limit`
- **account** 是 `/me` 相關，可能和現有 `insights_tracker.py` 重疊，**先查有沒有可複用的**

### 6.3 決策狀態（哪些已拍板、哪些批次 B 可重議）

**已拍板、不要再討論**：
- 扁平 layout（**不**改 src/ layout）
- publisher.py 放 repo root（**不**搬進 threads_cli/）
- ASCII 前綴（**不**用 emoji / unicode symbol）
- `--confirm --yes` 雙旗標（**不**改單旗標）

**情境依賴、批次 B 可以重議**：
- **argparse vs click / Typer**：批次 A 拍板 argparse 是因為當時指令少（3 個寫入）。批次 B 做完會有 ~10+ 指令（search / list / insights / replies / account / delete + 既有），**此時可重評**。決策要點：
  - argparse 維護成本：指令越多 `_build_parser()` 越冗長、dispatch table 仍可用
  - click 優勢：decorator 宣告指令、自動 help 排版、nested group 語法更清楚
  - Typer 優勢：type hint 直接當 schema、最少 boilerplate
  - **若重議採納**：用 dispatch table 的設計已預留遷移空間（每個 handler 都是獨立函式），遷移代價不高
- **`--limit` 預設 25 上限**：批次 A 是批次 B 才用到，批次 B 確認 Threads API 真實上限後可調整

### 6.4 下次 smoke test 的流程（已驗證可用）

1. Token scope GET /me（零副作用）
2. pytest 回歸
3. Entry points 在 PATH
4. dry-run 不發
5. Error-path（Token missing、flag 組合錯誤）
6. **授權後**實發 + DELETE（逐一 post_id 追蹤）
7. UI 視覺驗證（只有使用者能做）
8. 寫 `docs/superpowers/handoffs/YYYY-MM-DD-*-smoke.md`

---

## 附：連結

- Spec：`docs/superpowers/specs/2026-04-15-threads-cli-packaging-design.md`
- Plan：`docs/superpowers/plans/2026-04-15-threads-cli-packaging.md`
- Smoke handoff：`docs/superpowers/handoffs/2026-04-15-threads-cli-smoke.md`
- CLI Research：`docs/dev/cli-anything-research.md`
- API 探索：`docs/dev/api-exploration-results.md`
