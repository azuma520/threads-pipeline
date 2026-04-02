**主要發現**

1. `P0` 目前的 SQLite 資料不足以支撐 spec 裡最核心的幾個分析結論，這不是實作難度問題，是資料根本不存在。Spec 要輸出「高/低表現集群」「定位一致性百分比」「最佳發文時段（前 3 小時互動率）」「回覆互動習慣」「暖場建議」等，但現有資料只有每日快照的貼文 insights 與帳號 insights，且貼文只存 50 字 preview，不存完整文案、主題標籤、發文後分時序列，也不存作者主動回覆行為。[spec](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/superpowers/specs/2026-04-02-post-advisor-design.md#L54) [spec](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/superpowers/specs/2026-04-02-post-advisor-design.md#L63) [spec](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/superpowers/specs/2026-04-02-post-advisor-design.md#L68) [schema](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/dev/data-model.md#L11) [schema](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/dev/data-model.md#L83) [tracker](/C:/Users/user/OneDrive/桌面/threads_pipeline/insights_tracker.py#L31) [tracker](/C:/Users/user/OneDrive/桌面/threads_pipeline/insights_tracker.py#L170)  
可行修正：先把 `advisor analyze` 降級為「現況摘要 + 近 N 天趨勢 + Top posts 特徵觀察」，或先擴 schema，至少新增 `full_text`、`content_tag/category`、`post_hour_local`、`snapshot_time`、`reply_outbound_count`、發文後 1h/3h/24h 的分段快照。

2. `P0` 「最佳發文時段」的算法描述目前不可落地。Spec 明寫要用「歷史前 3 小時互動率」推時段，但現有資料模型只有每天抓一次當下總 views/likes/replies/reposts/quotes，沒有發文後 3 小時內的觀測點，所以無法回推出 early velocity。[spec](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/superpowers/specs/2026-04-02-post-advisor-design.md#L63) [schema](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/dev/data-model.md#L54) [tracker](/C:/Users/user/OneDrive/桌面/threads_pipeline/insights_tracker.py#L98)  
可行修正：要嘛把需求改成「歷史高表現貼文的發文時段分布」，要嘛新增排程，在發文後固定於 `+1h/+3h/+24h` 補抓快照。

3. `P0` `advisor review` 會把錯的 context 配到錯的草稿。Spec 規定一律讀「最新 analysis」與「同名 plan」，但沒有定義 draft 與 analysis 的關聯鍵，也沒有處理同一天多主題、多版本 plan、草稿改名、手動指定分析檔的情境。這在實務上很容易審錯稿。[spec](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/superpowers/specs/2026-04-02-post-advisor-design.md#L152) [spec](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/superpowers/specs/2026-04-02-post-advisor-design.md#L158)  
可行修正：在 `plan.md` 與 `draft.txt` frontmatter 加 `topic_id`、`analysis_id`、`created_at`；CLI 支援 `--analysis-path` / `--plan-path` 明確覆寫；若自動推斷失敗就中止，不要默默退回「最新」。

4. `P1` Codex CLI subprocess 整合規格不夠具體，實作時很容易變成脆弱的「把 prompt 丟進 stdout 然後賭格式」。Spec 只寫「組合 prompt → 呼叫 codex subprocess → 解析輸出」，但沒有定義命令格式、timeout、重試、stderr 處理、非 0 exit code、UTF-8、長 prompt 上限、固定輸出 schema、版本相容策略。[spec](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/superpowers/specs/2026-04-02-post-advisor-design.md#L156) [analyzer](/C:/Users/user/OneDrive/桌面/threads_pipeline/analyzer.py#L47)  
可行修正：先把 subprocess contract 寫死，例如「只接受 JSON 輸出」「明確 schema 驗證」「timeout 與 retry policy」「stdout/stderr logging」「版本檢查」。另外補一層 parser，不要直接信任模型字串。

5. `P1` 目前規格把可重現性壓在 repo 外部的互動式 skill 上，這會讓流程不可測、不可測試、不可 CI。`/threads-algorithm-skill` 是互動步驟，spec 沒有把 plan 的必要欄位、生成規則、失敗回退、版本固定下來；`copywriting-frameworks.md` 甚至還寫成「可放 skill references 旁或專案 docs/references」，位置不唯一。[spec](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/superpowers/specs/2026-04-02-post-advisor-design.md#L19) [spec](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/superpowers/specs/2026-04-02-post-advisor-design.md#L201)  
可行修正：把 review 依賴的 reference 全部 vendor 到 repo；定義 `plan.md` 最低 schema；skill 只負責互動，不負責提供唯一真實規格。

6. `P1` 規格要求「不動現有 `analyzer.py` / `insights_tracker.py`」，但 `advisor.py` 又需要大量重用它們的能力，這會逼出重複邏輯與日後漂移。像載入 config、找 DB、取 top posts、算 trend、subprocess error handling，本來就已經在現有模組各自存在。[spec](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/superpowers/specs/2026-04-02-post-advisor-design.md#L250) [main](/C:/Users/user/OneDrive/桌面/threads_pipeline/main.py#L35) [tracker](/C:/Users/user/OneDrive/桌面/threads_pipeline/insights_tracker.py#L144) [analyzer](/C:/Users/user/OneDrive/桌面/threads_pipeline/analyzer.py#L33)  
可行修正：允許小幅重構，抽出 `config loading`、`db query helpers`、`cli runner` 共用模組，再做 `advisor.py`。

7. `P1` 現有資料也無法可靠支撐「定位一致性百分比」。你沒有歷史貼文的 canonical topic/category，只存 `text_preview` 50 字；而 trend analyzer 的分類是針對外部搜尋結果，不是針對自己帳號貼文，也沒有回寫 SQLite。[schema](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/dev/data-model.md#L17) [tracker](/C:/Users/user/OneDrive/桌面/threads_pipeline/insights_tracker.py#L106) [analyzer](/C:/Users/user/OneDrive/桌面/threads_pipeline/analyzer.py#L33)  
可行修正：若要算一致性，至少需要對自家歷史貼文做一次離線分類並持久化結果，否則只能輸出定性觀察，不該輸出百分比。

8. `P2` 空資料與冷啟動情境沒有定義。`get_trend` 少於 2 筆就回 `None`，新帳號、剛啟用功能、抓取失敗那天，都會讓報告區塊缺資料；spec 沒定義 UI/文案上的 degraded mode。[tracker](/C:/Users/user/OneDrive/桌面/threads_pipeline/insights_tracker.py#L144) [schema](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/dev/data-model.md#L81)  
可行修正：在 spec 補上三種狀態。
正常模式：有 7 天資料。  
降級模式：只有 1 天資料，只輸出快照。  
無資料模式：只輸出待建立追蹤的提示，不做策略結論。

9. `P2` Windows 檔名與 topic 命名規則沒定義，`drafts/[topic].plan.md` / `[topic].txt` 很容易踩到非法字元、重名、emoji、全形符號或過長路徑問題。[spec](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/superpowers/specs/2026-04-02-post-advisor-design.md#L131) [spec](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/superpowers/specs/2026-04-02-post-advisor-design.md#L237)  
可行修正：topic 只當顯示名，實體檔案一律用 slug 或 UUID，並在 frontmatter 保存原始標題。

10. `P2` SQLite 讀寫競爭未處理。現有 pipeline 會寫入 `threads.db`，未來 `advisor analyze` 同時讀取同一 DB 時，若剛好碰到排程寫入，可能遇到 lock 或讀到半更新狀態；spec 完全沒提交易隔離與 busy timeout。[tracker](/C:/Users/user/OneDrive/桌面/threads_pipeline/insights_tracker.py#L80) [main](/C:/Users/user/OneDrive/桌面/threads_pipeline/main.py#L135)  
可行修正：read path 使用 read-only connection、設定 `busy_timeout`，並把 `analyze` 視為只讀查詢流程。

11. `P2` Prompt context 容量風險被低估。`review` 要同時塞 analysis、plan、演算法 reference、16+1 文案框架、draft；analysis 長期累積後很容易超出 CLI 舒適範圍，且沒有摘要策略。[spec](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/superpowers/specs/2026-04-02-post-advisor-design.md#L137) [spec](/C:/Users/user/OneDrive/桌面/threads_pipeline/docs/superpowers/specs/2026-04-02-post-advisor-design.md#L155)  
可行修正：先把 analysis 輸出拆成「完整報告」與「review 摘要 JSON」兩層，review 只讀摘要版。

12. `P2` 目前 repo 已明確記錄 Threads Standard Access 的限制，這代表 spec 現階段只能做「自家帳號歷史內容顧問」，不能隱含外部市場洞察。若需求方期待 Audience Affinity 來自同領域公開內容或趨勢比較，現在做不到。[CLAUDE.md](/C:/Users/user/OneDrive/桌面/threads_pipeline/CLAUDE.md#L77)  
可行修正：把 V2.5 的產品定位改寫清楚。
現在版：只用自家歷史內容與帳號成效。  
Advanced Access 後：才加入外部熱門貼文與競品對照。

**缺少的邊界情境**

- analysis 檔不存在、plan 檔不存在、draft 為空字串、draft 過長、draft 含多段主題切換時，review 要怎麼退化處理，spec 沒寫。
- `post_insights` 可能含 views=0，互動率分母為 0 的呈現規則沒寫。
- 刪文、隱藏文、引用文、回覆文是否納入歷史分析沒定義；這會直接影響 Top 5 與定位判讀。
- 時區只在 `config` 裡存在，但 `posted_at` 是 API timestamp；分析時要用 UTC 還是 `Asia/Taipei`，spec 沒明講，時段分析會被搞錯。
- review 是否要檢查「與近期自己貼文過度重複」沒寫，實務上這很重要。

**建議先補的規格**

- 定義 `advisor analyze` 第一版只保證哪些欄位與結論，哪些先不做。
- 定義 `plan.md` frontmatter schema。
- 定義 `review` 的 subprocess input/output schema 與失敗回退。
- 定義 artifact 關聯方式，不要靠「最新檔案」。
- 定義資料不足時的降級輸出，而不是輸出看似精準的百分比。

整體判斷：這份 spec 的方向是對的，但目前把「可分析的深度」寫得比現有資料能力高一個層級。若不先收斂成可由現有 SQLite 支撐的版本，實作很可能會變成用少量資料包裝出高確信結論，這是最大風險。