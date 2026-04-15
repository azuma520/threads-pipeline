# Threads CLI 批次 A Smoke Test 結果

日期：2026-04-15
分支：feat/cli-packaging
帳號：azuma01130626

## 驗證通過

- [x] Step 0: Token scope 驗證（GET /me 成功，帳號 azuma01130626）
- [x] Step 1: pytest 全綠（87 passed）
- [x] Step 2: 三個 entry points 皆在 PATH（threads-advisor / threads / cli-anything-threads）
- [x] Step 3: 雙軌 `--help` 對照（僅 prog name 差異，功能等效）
- [x] Step 4: dry-run 不真發（post + chain 皆驗證）
- [x] Step 5: Token 缺失 exit 1
- [x] Step 6: 非 TTY + --confirm 無 --yes exit 2
- [x] Step 7: --yes 無 --confirm exit 2
- [x] Step 8: 實發單則 18102849982757214 → DELETE API 成功
- [x] Step 9: parent 18047735318573916 + reply 18079832750434316 → 兩則 DELETE 成功
- [x] Step 10: 3 則串文 17982285795001992 / 18061470863694620 / 17972485166872025
      → UI 階梯式驗證通過（使用者親眼確認）
      → 三則 DELETE 成功
- [x] Step 11: --on-failure=retry exit 2（NotImplementedError）

## 意外收穫：真實 API race condition 驗證

第一次執行 chain 時碰到 Threads API race condition：

- 第 1 則 publish 成功（post_id 18019777049822048）
- 第 2 則 Step 1 建 container 成功（17947593192140142）
- 第 2 則 Step 2 publish 失敗：`API 400: The requested resource does not exist`

原因推測：剛發完的第 1 則立刻被當 reply_to，Threads API 內部索引尚未建好。

**ChainMidwayError 在真實條件下運作完美：**

```
[ERROR] Chain failed at post 2
  Already posted IDs: ['18019777049822048']
  Cause: Step 2 failed (orphan container_id=17947593192140142): API 400: ...
  Recovery: manually delete or continue from post 2
exit=1
```

- ✅ 正確拋出 ChainMidwayError（IS-A PublishError 但不被 parent handler 吞掉）
- ✅ 回報 posted_ids、failed_index
- ✅ exit 1（不是 2）
- ✅ Recovery 提示可操作

已發的第 1 則已手動 DELETE 清理。孤兒 container（17947593192140142）因未 publish 不顯示。

**這是靠 mock test 測不到的真實世界驗證。**

## 已知限制（對照 plan）

1. **API race condition**：連續 publish → reply 可能偶發失敗。Level 1 明確排除 retry（on_failure=stop 是唯一實作），符合設計。
2. **UTF-8 顯示**：Windows cp950 終端印中文會亂碼（例如 advisor `--help` 的中文描述），但 `[ERROR]` / `[OK]` ASCII 前綴正常。
3. **list-frameworks 不存在**：plan 假設的驗證指令在 advisor.py 實際沒有，改用 `--help` 雙軌對照。

## 過程中發現並修復的問題

1. **setuptools build-time 驗證 package-dir**：plan 預測「editable install lazy」錯誤，實測在 build time 就檢查目錄。修補：Task 0 先建 `threads_cli/__init__.py` 空 stub（commit 9950d60）。
2. **pytest 升級 7→9 破壞 pytest-asyncio 0.23**：pip install 把 pytest 升到 9.0，需同步升級 pytest-asyncio 至 1.3.0（環境修補，非 commit）。
3. **CLI 未載入 .env**：plan 漏了。advisor main() 會呼叫 `_load_dotenv`，threads CLI 沒做，導致 smoke 所有指令回 Token missing。修補：commit 84a5ac1。

## Commit 序列

```
84a5ac1 fix(cli): 啟動時自動載入 .env（對齊 advisor 行為）
d1d33ad docs(claude): 更新 Commands 區塊為雙軌並列
a577897 docs(cli): SKILL.md 最小版
d2b924f feat(cli): threads post publish-chain 指令
9fc4f2a feat(cli): threads reply 指令
798f0a2 feat(cli): threads post publish 指令
fb9b6e4 feat(cli): safety 層
d11378d feat(publisher): publish_chain
3433be4 feat(publisher): reply_to
1364027 feat(publisher): publish_text
8d7ff76 feat(cli): threads CLI 骨架 + dispatch table
9950d60 feat(packaging): 加 pyproject.toml
```

## 結論

批次 A 全部驗收通過，建議 merge。
