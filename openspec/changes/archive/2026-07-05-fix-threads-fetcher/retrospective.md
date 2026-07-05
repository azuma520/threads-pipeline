# Retrospective: fix-threads-fetcher

> Written: 2026-07-05 (after verify passed)
> Commit range: `34eaaeb..dc81085`
> Worktree: 就地於 `fix-threads-fetcher` branch（未開額外 worktree，見 §4）

---

## 0. Evidence

- **Commit range**: `34eaaeb..dc81085`（11 commits）
- **Diff size**: +3553 / -10 across 23 files（其中 code 僅 2 檔：`scripts/fetch_threads_post.py` +176、`tests/test_fetch_threads_post.py` +191；其餘為 openspec change artifacts + bridge schema 首次引入）
- **Tasks done**: 8/8（+1 項 `[~]` deferred，見 verify §7）
- **Active hours**: ~1.5h（含研究/實測/審查）
- **Subagent dispatches**: 6（Explore 脈絡調查 ×1、implementer ×4 批、strict-reviewer final ×1）+ Codex gpt-5.5 設計審查 1 次（外部第三方）
- **New external dependencies**: none（og fallback 用 stdlib `urllib.request` + `html.parser`）
- **Bugs encountered post-merge**: none（尚未 merge）；apply 內 final review 抓到 2 個 og 正則邊界 bug，merge 前已修（commit `f26199b`）
- **OpenSpec validate state at archive**: pass
- **Test coverage signal**: pytest 全套 243 passed（模組 51 passed），0 失敗，零回歸

Commit chain（時序）:

```
34eaaeb plan: openspec change 初建（含 bridge schema）
4110e16 test: pin classify behavior for foreign top-level non-reply posts
e2d9da9 fix: mobile browser fingerprint（繞過匿名封鎖）
565ccec feat: drop foreign class-A posts（污染防護）
b2433a0 feat: og meta extraction
7a2c981 feat: og fallback HTTP fetch + partial renderer
bfbb972 feat: relay.json optional in write_output
31622fe feat: og fallback chain + 0/3/2 exit code
221c22d docs: mobile fingerprint / fallback chain / exit codes
f26199b fix: rewrite og extraction with html.parser（review 抓的 quote/gt 邊界）
dc81085 plan: mark tasks done + D5 apply boundary
```

---

## 1. Wins

- [evidence: e2d9da9 + planning 8 條實測] 核心修法在**寫 plan 前就端到端實測驗證**（8 條真實 URL、8/8），不是紙上設計——使用者質疑「確定能解決嗎」時有硬證據回應。
- [evidence: f26199b + strict-reviewer] Final review 抓到 og 正則兩個真實邊界 bug（ASCII 單引號截斷、content 含 `>` 截斷），改 `html.parser` 一次解決，且 characterization test 先 FAIL 證 bug 真實再 PASS。降級保險絲路徑在 merge 前就補實。
- [evidence: 565ccec + 8 條實測] 污染防護從「以為是常態」被實測降級為「偶發」（僅首樣本觸發），避免過度設計，但仍保留（成本低）。
- [evidence: Codex gpt-5.5 審查] 第三方設計審查抓到 og guard 盲點（①）——原設計「og 非空即 partial」會讓降級鏈掩蓋主管道壞損信號，採納為 D7 author guard。

## 2. Misses

- 🟡 [painful | evidence: f26199b] og 解析第一版用手寫正則，final review 才抓到引號/`>` 邊界。TDD 的測試（`test_extract_og_fields_attr_order_and_single_quotes`）名稱宣稱覆蓋「引號」卻只驗 delimiter 種類、沒驗內嵌引號——**假綠**。教訓：測試名承諾的覆蓋要與 assertion 實際覆蓋一致。
- 📌 [nit | evidence: verify §7 第三列] 8 條實測未刻意涵蓋多圖/影片/引用貼文型態，行動版 Relay 多媒體結構為殘留測試 gap（非阻塞，見 §6 follow-up）。

## 3. Plan deviations

| Plan task | What changed | Why |
|-----------|--------------|-----|
| Task 3 Step 3b | 未加 code/thread-root 錨定，維持 username-only 過濾 | 實測 8 條零同作者污染，Relay root 欄位檢查成本 > 收益；design D5 已記為接受邊界 |
| Task 4 | 正則版 → 改 `html.parser`（review 後） | final review 抓到正則兩個邊界 bug，parser 更穩健且零新依賴 |
| Task 8 Step 5 | deferred `[~]`，未人工跑 | 主管道已由 orchestrator 8 條實測等價覆蓋，partial 由 monkeypatch 覆蓋（verify §7） |

## 4. Skill / workflow compliance

| Skill | Used |
|-------|------|
| superpowers:brainstorming | ✓ |
| superpowers:writing-plans | ✓ |
| superpowers:using-git-worktrees | ✓（就地判斷，見下） |
| superpowers:subagent-driven-development | ✓ |
| (transitive) superpowers:test-driven-development | ✓（每 task RED-GREEN） |
| (transitive) superpowers:requesting-code-review | ✓（final strict-reviewer） |
| superpowers:finishing-a-development-branch | ⏳ 待執行（本 retro 後） |

### Deliberately Skipped Skills

- **`superpowers:using-git-worktrees`（未開實體 worktree，就地於 feature branch 實作）**
  - **What was skipped**：skill 的 Step 1 建立實體 git worktree 這一 sub-step；Step 0 偵測與隔離意圖有遵循。
  - **Why this cycle**：8 個 task 序列改**同一支** `scripts/fetch_threads_post.py`（彼此依賴、無並行 subagent 同檔），worktree 的並行隔離價值不存在；且 repo 在 D: 跨 drive，Windows worktree 增加失敗面。已在專用 `fix-threads-fetcher` feature branch（對 main 已隔離，Step 0 偵測 `GIT_DIR==GIT_COMMON` 的 normal checkout 但在非 main branch）。
  - **How to prevent recurrence**：`scope-judgment rule`——「單檔序列實作、無並行 subagent 寫同檔」時，feature branch 隔離已達成 worktree 的保護目的，就地實作是合理判斷；schema apply 要 worktree 的真正動機是「並行 subagent 不衝突」，該動機缺席時就地不違背意圖。若未來 cycle 有並行寫不同檔的 subagent，才需實體 worktree。

## 5. Surprises

- 行動版 UA **單獨**（純 curl）拿不到 Relay，只有 og；但 **Playwright + 行動版 context**（含 `is_mobile`）能拿到完整 Relay——差異在 JS 執行 + 完整 mobile context 而非單純 UA 字串。若只試 curl 行動 UA 會誤判「行動版也不行」。
- 真實 Threads 的 og content 是 entity-escaped（`>`→`&gt;`、引號 escape），所以 final review 抓的兩個正則 bug 在**真實資料上不觸發**——但降級鏈是保險絲，不能賭所有來源都 escape，仍值得修穩。

## 6. Promote candidates → long-term learning

- [ ] 🟡 **測試名/註解承諾的覆蓋範圍，要與 assertion 實際覆蓋一致——否則是假綠** → **Promote to memory** (type: feedback)
  > **Why**: 本 cycle `test_extract_og_fields_attr_order_and_single_quotes` 名稱宣稱驗「單雙引號」，實際只驗 delimiter 種類、漏了內嵌引號/`>`，兩個 og 正則 bug 因此漏測仍全綠，靠 final review 才抓到。
  > **How to apply**: 寫測試或審測試時，檢查測試名/註解承諾的 case 是否每個都有對應 assertion；TDD 的 GREEN 不代表覆蓋完整。

- [ ] 📌 **行動版抓 Threads 要用 Playwright mobile context（含 is_mobile），不是只換 UA 字串** → **Promote to project CLAUDE.md / line-import 備忘** (vault 端 `MEMORY.md` 或 fetcher 註記)
  > **Why**: 純 curl 行動 UA 只拿到 og、拿不到 Relay；容易誤判「行動版也失效」而放棄唯一可行路線。
  > **How to apply**: 未來 Threads fetcher 再壞、重新探索匿名支線時，區分「UA 字串」與「完整 mobile browser context」，後者才是關鍵。

- [ ] 📌 **多媒體型態（多圖/影片/引用貼文）行動版 Relay 結構未測** → **One-off**（follow-up 觀察，不 promote 成規則）
  > **Why**: 8 條實測未涵蓋，屬真空窗；但強行造 fixture 成本高於價值。
  > **How to apply**: 首次真實遇到多媒體貼文抓取異常時，dump Relay 觀察結構、補 fixture；在此之前不預先投入。

- [ ] 📌 **superpowers-bridge schema 首次在 vault 外部 code repo 試點成功** → **One-off**（記錄里程碑）
  > **Why**: 這是 CLAUDE.md 提到的「工程型 change 用 bridge schema 試點」首次實跑，走完 brainstorm→…→verify→retrospective 全流程，verify 硬依賴 git 在真 git repo 成立（vault 內錯配問題不存在）。
  > **How to apply**: 未來外部 code repo 的工程型 change 可沿用此路徑；vault 內非 git 場景仍用 skill-dev schema。
