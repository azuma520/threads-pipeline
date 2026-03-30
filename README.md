# Threads AI 趨勢收集 Pipeline

每日自動收集 Threads 上 AI/科技趨勢貼文，用 Claude 篩選分析，產出 Markdown 摘要報告。

## 使用方式

```bash
# 設定 .env
THREADS_ACCESS_TOKEN=你的token

# 執行
PYTHONUTF8=1 python -m threads_pipeline.main
```

## 架構

```
cron → Threads API keyword_search → 去重/清洗 → claude -p 分析 → Jinja2 Markdown 報告
```

## 檔案結構

```
threads_pipeline/
├── config.yaml         # 關鍵字、輸出路徑設定
├── main.py             # 進入點
├── threads_client.py   # Threads API 封裝
├── analyzer.py         # Claude 分析（claude -p）
├── report.py           # Jinja2 報告渲染
├── templates/          # Markdown 模板
└── tests/              # 測試（34 個）
```

## 需求

- Python 3.13+
- requests, pyyaml, jinja2
- Claude Code CLI（用於 AI 分析）
- Meta Threads API Access Token
