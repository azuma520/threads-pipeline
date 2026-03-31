# 測試指南

## 1. 測試結構

| 測試檔案 | 對應模組 | 測試類別數 | 測試方法數 | 重點 |
|---|---|---|---|---|
| `tests/test_threads_client.py` | `threads_pipeline.threads_client` | 3 | 9 | 貼文抓取、跨關鍵字去重、HTTP 重試邏輯 |
| `tests/test_analyzer.py` | `threads_pipeline.analyzer` | 5 | 14 | Prompt 組裝、JSON 解析、fallback、subprocess 整合 |
| `tests/test_report.py` | `threads_pipeline.report` | 3 | 11 | 分組排序、報告渲染、檔案寫入 |

### test_threads_client.py 類別明細

| 類別 | 方法數 | 說明 |
|---|---|---|
| `TestFetchPosts` | 4 | 整合測試：正常抓取、去重、空結果、部分關鍵字失敗 |
| `TestSearchKeyword` | 2 | 單元測試：回傳貼文列表、max_results 上限 |
| `TestRequestWithRetry` | 3 | 重試邏輯：第一次成功、500 觸發重試、超過上限拋出例外 |

### test_analyzer.py 類別明細

| 類別 | 方法數 | 說明 |
|---|---|---|
| `TestBuildPrompt` | 3 | prompt 包含所有貼文 ID、作者名稱、貼文內容 |
| `TestParseAnalysis` | 5 | 正確 JSON、markdown code block、畸形 JSON、空字串、分數範圍 |
| `TestFallbackAnalysis` | 1 | fallback 給所有貼文預設值 |
| `TestMergeAnalysis` | 2 | 按 ID 合併、缺少貼文時補 fallback |
| `TestAnalyzePosts` | 3 | 正常分析流程、subprocess 失敗使用 fallback、空列表 |

### test_report.py 類別明細

| 類別 | 方法數 | 說明 |
|---|---|---|
| `TestGroupAndSort` | 4 | 按分類分組、分類順序、組內降序、空列表 |
| `TestRenderReport` | 5 | 包含日期、包含分類標題、貼文數量、零貼文訊息、星星評分 |
| `TestSaveReport` | 2 | 正確建立檔案、輸出目錄不存在時自動建立 |

---

## 2. Mock 策略

### threads_client

- **`_search_keyword`**：在 `TestFetchPosts` 中以 `@patch("threads_pipeline.threads_client._search_keyword")` 隔離 Threads API 呼叫，讓 `fetch_posts` 的測試只驗證去重、錯誤處理等邏輯，而不發出真實網路請求。
- **`requests.Session.get`**：在 `TestRequestWithRetry` 中以 `@patch("requests.Session.get")` 控制 HTTP 回應，可模擬 200 成功或 500 失敗，測試重試次數與例外行為。
- **`time.sleep`**：重試測試同時以 `@patch("time.sleep")` 取消等待，避免測試因退避延遲（backoff）而拖慢執行速度。

### analyzer

- **`subprocess.run`**：在 `TestAnalyzePosts` 中以 `@patch("threads_pipeline.analyzer.subprocess.run")` 避免真正呼叫 `claude -p`，透過設定 `returncode`、`stdout`、`stderr` 來模擬 Claude CLI 的正常回覆與錯誤情境。
- **預製 JSON**：使用 `mock_claude_analysis_json` fixture 提供格式正確的 Claude 回覆字串，供解析與合併測試使用，確保測試結果可重現。

### report

- **`tempfile.TemporaryDirectory`**：在 `TestSaveReport` 中以暫存目錄取代真實輸出路徑，測試結束後自動清除，不留下任何殘餘檔案。

---

## 3. 共用 Fixture（conftest.py）

| Fixture 名稱 | 用途 |
|---|---|
| `mock_threads_response` | 模擬 Threads API `keyword_search` 的完整回應，包含 5 篇貼文與分頁游標 |
| `mock_threads_response_empty` | 模擬零結果的 API 回應（`{"data": []}`），用於測試空資料路徑 |
| `sample_posts` | 已清洗的 5 篇貼文列表，涵蓋四種分類的關鍵字，供 analyzer 與 report 測試使用 |
| `mock_claude_analysis_json` | 模擬 Claude 回覆的 JSON 字串，包含 5 篇貼文的分類、分數、摘要 |
| `analyzed_posts` | 組合自 `sample_posts` 與 `mock_claude_analysis_json`，已完成分析欄位合併的貼文列表，供 report 測試使用 |

---

## 4. 常用指令

```bash
# 跑全部測試
python -m pytest

# 跑單一檔案
python -m pytest tests/test_analyzer.py

# 跑單一測試類別
python -m pytest tests/test_analyzer.py::TestParseAnalysis

# 跑單一測試方法
python -m pytest tests/test_analyzer.py::TestParseAnalysis::test_valid_json

# 顯示詳細輸出
python -m pytest -v

# 只跑失敗的測試
python -m pytest --lf
```
