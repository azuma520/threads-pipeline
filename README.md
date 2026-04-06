# Threads AI 趨勢收集 Pipeline

每日自動收集 Threads 上 AI/科技趨勢貼文，用 Claude 篩選分析，產出 Markdown 摘要報告。

## 關於本專案

**Threads AI 趨勢收集 Pipeline** 是由鉦旺樂開發的自動化趨勢監測工具，專門用於追蹤 Meta Threads 平台上的 AI 與科技趨勢話題。

本工具透過 Threads Graph API **僅讀取公開貼文**，經由 AI 分析後產出結構化的趨勢摘要報告，協助使用者快速掌握產業動態。

### 功能概述

- 依關鍵字自動搜尋 Threads 公開貼文
- 去重與資料清洗
- 使用 Claude AI 進行內容篩選與分析
- 產出 Markdown 格式的每日趨勢報告

### API 使用範圍

本應用程式僅使用 Meta Threads Graph API 的以下功能：

- **關鍵字搜尋**：搜尋公開貼文
- **貼文讀取**：取得貼文內容、作者、時間戳記等公開資訊
- **不發布、不修改、不刪除**任何內容
- **不存取**任何非公開資料

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

## 隱私權政策

本應用程式尊重使用者隱私：

- **僅讀取公開資料**：只存取 Threads 上公開可見的貼文內容
- **不蒐集個人資料**：不儲存任何 Threads 使用者的個人身分資訊
- **資料用途單一**：蒐集的公開貼文僅用於趨勢分析與報告產出
- **不分享第三方**：分析結果僅供內部使用，不轉售或分享給第三方
- **資料保留**：產出的報告為彙整摘要，不保留原始貼文的完整資料副本

## 開發者資訊

- **公司名稱**：鉦旺樂
- **開發者**：楊東杰
- **聯絡信箱**：kyoe33@gmail.com
- **GitHub**：[github.com/azuma520](https://github.com/azuma520)

## 授權

MIT License
