## 1. SKILL.md ── Step 1 載入機制

- [ ] 1.1 在 Step 1 entry 段落加「載入 references/02-user-profile.md」instruction（Read 工具、internalize、不展開）
- [ ] 1.2 加 02-user-profile.md 不存在時的 fallback：提示 user 從 template copy + fill、不繼續 Step 1
- [ ] 1.3 加註記避免機械感（❌「我讀了你的 9 條內核」/ ✅ 直接進 dump）

## 2. SKILL.md ── Step 2 主線重定義

- [ ] 2.1 Step 2 entry 段落加 reread instruction：Section 7（4 維 + 樣子）+ Section 4（內核）
- [ ] 2.2 改寫 Step 2「抓主線」邏輯為三件事：角色設定（4 維）+ 個人經驗 + 個人觀察 / 心得
- [ ] 2.3 加 4 維 surface + 給 user 刪除法 verify 流程（不純開放問）
- [ ] 2.4 加抓完 4 維後對位 profile Section 7 樣子實例 surface 給 user 選的步驟
- [ ] 2.5 加「四個樣子都不像 → surface 新樣子、不擅自寫進 profile」邊界

## 3. SKILL.md ── Step 2.5 訪談 trigger

- [ ] 3.1 Step 2.5 entry 段落改寫為 4 條明確 trigger（觀察 / 動機 / 判斷 / 4 維 cover）
- [ ] 3.2 加諮詢式 vs 評估式對照（✅ 「我聽下來你那當下的觀察可能是 X、是這樣嗎？」/ ❌ 「你 dump 缺觀察、要補」）
- [ ] 3.3 加「沒有就沒有」原則明示（問了真沒有 agent 接受、不勉強補）

## 4. SKILL.md ── Step 3 角色偏移診斷

- [ ] 4.1 Step 3 entry 段落加 reread instruction：Section 5（紅線）+ Section 7（樣子對照）
- [ ] 4.2 加角色偏移診斷 3 項：踩紅線 / 預設 generic / 文風 vs 內核衝突
- [ ] 4.3 加「角色對位樣子」surface 步驟
- [ ] 4.4 加「surface 給 user 決定回 Step 2 / 2.5、skill 不擅自重啟」邊界

## 5. SKILL.md ── Step 5 / Step 8 reread（P2、跟 spec 同步）

- [ ] 5.1 Step 5 entry 段落加 reread instruction：Section 5（紅線）+ Section 4（內核）
- [ ] 5.2 Step 8 entry 段落加 reread instruction：Section 5（紅線）+ Section 6（表達偏好）

## 6. SKILL.md ── setup section

- [ ] 6.1 在 SKILL.md 適當位置（建議 top 或 references list）加 setup section
- [ ] 6.2 寫一句說明為什麼需要 Layer 1（避免 agent 預設 generic 角色）
- [ ] 6.3 寫 copy 命令 / 路徑指引
- [ ] 6.4 寫 fill 指引（指向 template placeholder）
- [ ] 6.5 寫 gitignore 註記（實際 02-user-profile.md 不會推上 GitHub）

## 7. 既有 reference 同步檢查

- [ ] 7.1 verify `references/00-philosophy.md` 不需改（既有 5 原則覆蓋 sense > 機械 / 訪談 + 刪除法 / 沒有就沒有）
- [ ] 7.2 verify `references/01-user-expression.md` 不需改（user voice 跟 Layer 1 用戶角色設定資料切開）
- [ ] 7.3 cross-check `references/02-user-profile.template.md` 跟 spec 對齊（Section 4 / 5 / 6 / 7 結構描述一致）

## 8. 測試

- [ ] 8.1 SKILL.md smoke test：用一段 fresh dump 跑 Step 1-3、確認 agent 在 Step 1 載入 profile、Step 2 抓 3 件事、Step 3 跑角色偏移診斷
- [ ] 8.2 fallback test：手動 rename 02-user-profile.md、確認 agent 提示 user 從 template copy
- [ ] 8.3 acceptance check：跟 user 走過一輪實際 dump、確認 5/8 痛點（agent 預設 generic 角色）不重現

## 9. openspec validate + 收尾

- [ ] 9.1 跑 `openspec validate --all --json`、確認 spec / proposal / design / tasks 全綠
- [ ] 9.2 update tasks.md checkbox 全部 [x]
- [ ] 9.3 commit + push（feature branch、apply 階段走 worktree）
- [ ] 9.4 verify.md / retrospective.md（apply 階段完成後另寫）
