"""共用 mock fixtures。"""

import pytest


@pytest.fixture
def mock_threads_response():
    """模擬 Threads API keyword_search 回應。"""
    return {
        "data": [
            {
                "id": "17841400000000001",
                "text": "Claude 4 剛發布，Agent 能力大幅提升，可以自主完成複雜的多步驟任務",
                "username": "ai_updates_tw",
                "timestamp": "2026-03-29T14:30:00+0000",
                "like_count": 234,
                "permalink": "https://www.threads.net/@ai_updates_tw/post/ABC001",
            },
            {
                "id": "17841400000000002",
                "text": "OpenAI 宣布 GPT-5 將在下個月發布，主打多模態推理能力",
                "username": "tech_news_daily",
                "timestamp": "2026-03-29T10:15:00+0000",
                "like_count": 512,
                "permalink": "https://www.threads.net/@tech_news_daily/post/ABC002",
            },
            {
                "id": "17841400000000003",
                "text": "教學：如何用 LangChain + Claude 建立 RAG pipeline，含完整程式碼",
                "username": "dev_teacher",
                "timestamp": "2026-03-29T08:00:00+0000",
                "like_count": 89,
                "permalink": "https://www.threads.net/@dev_teacher/post/ABC003",
            },
            {
                "id": "17841400000000004",
                "text": "AI 不會取代工程師，但會用 AI 的工程師會取代不會的。這句話已經從預言變成現實了",
                "username": "startup_cto",
                "timestamp": "2026-03-29T16:45:00+0000",
                "like_count": 1023,
                "permalink": "https://www.threads.net/@startup_cto/post/ABC004",
            },
            {
                "id": "17841400000000005",
                "text": "新工具推薦：Cursor 0.50 更新了 Agent 模式，寫程式效率又提升一個層級",
                "username": "tools_weekly",
                "timestamp": "2026-03-29T12:00:00+0000",
                "like_count": 178,
                "permalink": "https://www.threads.net/@tools_weekly/post/ABC005",
            },
        ],
        "paging": {
            "cursors": {"after": "xyz123"},
        },
    }


@pytest.fixture
def mock_threads_response_empty():
    """模擬零結果的 API 回應。"""
    return {"data": []}


@pytest.fixture
def sample_posts():
    """已清洗的貼文列表（5 篇，涵蓋四種分類）。"""
    return [
        {
            "id": "17841400000000001",
            "text": "Claude 4 剛發布，Agent 能力大幅提升",
            "username": "ai_updates_tw",
            "timestamp": "2026-03-29T14:30:00+0000",
            "like_count": 234,
            "permalink": "https://www.threads.net/@ai_updates_tw/post/ABC001",
            "keyword_matched": "Claude",
        },
        {
            "id": "17841400000000002",
            "text": "OpenAI 宣布 GPT-5 將在下個月發布",
            "username": "tech_news_daily",
            "timestamp": "2026-03-29T10:15:00+0000",
            "like_count": 512,
            "permalink": "https://www.threads.net/@tech_news_daily/post/ABC002",
            "keyword_matched": "GPT",
        },
        {
            "id": "17841400000000003",
            "text": "教學：如何用 LangChain + Claude 建立 RAG pipeline",
            "username": "dev_teacher",
            "timestamp": "2026-03-29T08:00:00+0000",
            "like_count": 89,
            "permalink": "https://www.threads.net/@dev_teacher/post/ABC003",
            "keyword_matched": "LLM",
        },
        {
            "id": "17841400000000004",
            "text": "AI 不會取代工程師，但會用 AI 的工程師會取代不會的",
            "username": "startup_cto",
            "timestamp": "2026-03-29T16:45:00+0000",
            "like_count": 1023,
            "permalink": "https://www.threads.net/@startup_cto/post/ABC004",
            "keyword_matched": "AI",
        },
        {
            "id": "17841400000000005",
            "text": "新工具推薦：Cursor 0.50 更新了 Agent 模式",
            "username": "tools_weekly",
            "timestamp": "2026-03-29T12:00:00+0000",
            "like_count": 178,
            "permalink": "https://www.threads.net/@tools_weekly/post/ABC005",
            "keyword_matched": "Agent",
        },
    ]


@pytest.fixture
def mock_claude_analysis_json():
    """模擬 Claude 回覆的 JSON 字串。"""
    return """[
    {"id": "17841400000000001", "category": "產業動態", "score": 5, "summary": "Claude 4 發布，Agent 能力大升級"},
    {"id": "17841400000000002", "category": "產業動態", "score": 4, "summary": "GPT-5 下月發布，主打多模態"},
    {"id": "17841400000000003", "category": "教學", "score": 3, "summary": "LangChain + Claude RAG 教學"},
    {"id": "17841400000000004", "category": "觀點", "score": 4, "summary": "會用 AI 的工程師將取代不會的"},
    {"id": "17841400000000005", "category": "新工具", "score": 3, "summary": "Cursor 0.50 Agent 模式更新"}
]"""


@pytest.fixture
def analyzed_posts(sample_posts, mock_claude_analysis_json):
    """已分析完成的貼文列表。"""
    import json

    analysis = json.loads(mock_claude_analysis_json)
    analysis_map = {str(a["id"]): a for a in analysis}

    for p in sample_posts:
        a = analysis_map[str(p["id"])]
        p["category"] = a["category"]
        p["score"] = a["score"]
        p["summary"] = a["summary"]

    return sample_posts
