"""Claude AI 分析模組：分類、評分、摘要。使用 claude -p 執行分析。"""

import json
import logging
import subprocess

logger = logging.getLogger(__name__)

CATEGORIES = ["新工具", "產業動態", "教學", "觀點"]

ANALYSIS_PROMPT = """你是一個 AI/科技趨勢分析助手。請分析以下 Threads 貼文，對每篇貼文提供：

1. **分類**（僅限以下四類之一）：新工具 / 產業動態 / 教學 / 觀點
2. **趨勢分數**（1-5 分）：
   - 5 = 重大突破或產業轉折
   - 4 = 值得關注的新發展
   - 3 = 有參考價值
   - 2 = 一般資訊
   - 1 = 噪音或低相關
3. **一行摘要**（繁體中文，20 字以內）

請以 JSON 陣列格式回覆，每個元素包含：
{{"id": "貼文ID", "category": "分類", "score": 分數, "summary": "摘要"}}

貼文列表：
---
{posts_block}
---

僅回覆 JSON 陣列，不要加其他文字。"""


def analyze_posts(posts: list[dict], config: dict) -> list[dict]:
    """批次送 claude -p 分析，回傳含分類/評分/摘要的貼文列表。"""
    if not posts:
        return []

    # 分批處理（每批最多 50 篇）
    batch_size = 50
    all_analysis = []

    for i in range(0, len(posts), batch_size):
        batch = posts[i : i + batch_size]
        prompt = _build_prompt(batch)

        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--model", "haiku"],
                capture_output=True,
                text=True,
                timeout=120,
                encoding="utf-8",
            )
            if result.returncode != 0:
                raise RuntimeError(f"claude -p 失敗: {result.stderr}")
            analysis = _parse_analysis(result.stdout)
        except Exception as e:
            logger.warning("Claude 分析失敗: %s，使用 fallback", e)
            analysis = _fallback_analysis(batch)

        all_analysis.extend(analysis)

    return _merge_analysis(posts, all_analysis)


def _build_prompt(posts: list[dict]) -> str:
    """組裝分析 prompt。"""
    lines = []
    for p in posts:
        likes = p.get("like_count", 0)
        lines.append(f"[ID: {p['id']}] @{p['username']} (❤️ {likes})")
        lines.append(p.get("text", ""))
        lines.append("---")

    posts_block = "\n".join(lines)
    return ANALYSIS_PROMPT.format(posts_block=posts_block)


def _parse_analysis(response_text: str) -> list[dict]:
    """解析 Claude 回覆的 JSON。失敗回傳空列表（由呼叫端處理 fallback）。"""
    # 嘗試直接解析
    text = response_text.strip()

    # 移除可能的 markdown code block 包裝
    if text.startswith("```"):
        lines = text.split("\n")
        # 去掉首尾的 ``` 行
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    logger.warning("無法解析 Claude 回覆為 JSON")
    return []


def _fallback_analysis(posts: list[dict]) -> list[dict]:
    """分析失敗時的 fallback：給予預設值。"""
    return [
        {
            "id": p["id"],
            "category": "觀點",
            "score": 2,
            "summary": "（AI 分析失敗，請手動查看）",
        }
        for p in posts
    ]


def _merge_analysis(posts: list[dict], analysis: list[dict]) -> list[dict]:
    """將分析結果合併回貼文 dict。未匹配的貼文給 fallback 值。"""
    analysis_map = {str(a["id"]): a for a in analysis}

    merged = []
    for p in posts:
        pid = str(p["id"])
        if pid in analysis_map:
            a = analysis_map[pid]
            p["category"] = a.get("category", "觀點")
            p["score"] = a.get("score", 2)
            p["summary"] = a.get("summary", "（無摘要）")
        else:
            p["category"] = "觀點"
            p["score"] = 2
            p["summary"] = "（AI 分析失敗，請手動查看）"
        merged.append(p)

    return merged
