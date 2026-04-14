"""advisor plan 串文骨架生成器。"""

from __future__ import annotations

import json
import logging
import platform
import re
import subprocess
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_CLAUDE_TIMEOUT_SEC = 60

_ILLEGAL_FILENAME = re.compile(r'[/\\:*?"<>|]')
_WHITESPACE = re.compile(r"\s+")
_MAX_SLUG_LEN = 20


def slugify(topic: str) -> str:
    """把題目轉成檔名安全的 slug。保留中文，英文轉小寫，長度 ≤20。"""
    if not topic:
        return _timestamp_slug()
    cleaned = _ILLEGAL_FILENAME.sub("", topic).strip()
    cleaned = _WHITESPACE.sub("-", cleaned)
    cleaned = cleaned.lower()
    cleaned = cleaned[:_MAX_SLUG_LEN]
    if not cleaned or all(c == "-" for c in cleaned):
        return _timestamp_slug()
    return cleaned


def _timestamp_slug() -> str:
    now = datetime.now(timezone.utc)
    return f"plan-{now.strftime('%Y%m%d-%H%M')}"


_FRAMEWORK_ROW = re.compile(
    r"^\|\s*(\d{2})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$",
    re.MULTILINE,
)


def _slice_structure_overview(md: str) -> str:
    """只取『## 結構總覽』到下一個 '## ' 之間的文字，避免誤吃『4 類結尾』等其他表格。"""
    m = re.search(r"^##\s*結構總覽\s*$", md, re.MULTILINE)
    if not m:
        return md  # fallback：整份都吃（regex 對中文第一欄的結尾表天然不匹配，但加 anchor 更穩）
    start = m.end()
    next_section = re.search(r"^##\s+", md[start:], re.MULTILINE)
    end = start + next_section.start() if next_section else len(md)
    return md[start:end]


def list_frameworks(md: str) -> list[dict]:
    """從 frameworks markdown 解析出所有框架。只吃「結構總覽」表，忽略結尾類型表。"""
    section = _slice_structure_overview(md)
    out = []
    for m in _FRAMEWORK_ROW.finditer(section):
        fw_id = int(m.group(1))
        out.append({
            "id": fw_id,
            "name": m.group(2).strip(),
            "formula": m.group(3).strip(),
            "when_to_use": m.group(4).strip(),
        })
    return out


def extract_framework_section(md: str, key: int | str) -> str | None:
    """依編號或名稱取出單一框架的描述。回傳 '編號 名稱 | 公式 | 適用場景' 的多行字串。"""
    frameworks = list_frameworks(md)
    for fw in frameworks:
        if (isinstance(key, int) and fw["id"] == key) or (isinstance(key, str) and fw["name"] == key):
            return (
                f"編號：{fw['id']:02d}\n"
                f"名稱：{fw['name']}\n"
                f"公式：{fw['formula']}\n"
                f"適用場景：{fw['when_to_use']}"
            )
    return None


class PlannerError(Exception):
    """planner 錯誤基類。"""


def parse_suggestions_json(stdout: str) -> list[dict]:
    """解析 Stage 1 的 JSON 回應。失敗直接 raise PlannerError（不做 fallback）。"""
    text = stdout.strip()
    # 容錯：LLM 常常忘了「不要 markdown code fence」指示
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise PlannerError(f"JSON 解析失敗：{e}；原始輸出：{stdout[:200]}") from e
    if "suggestions" not in data or not isinstance(data["suggestions"], list):
        raise PlannerError(f"缺少 suggestions 陣列；原始輸出：{stdout[:200]}")
    out = []
    for i, s in enumerate(data["suggestions"], start=1):
        if "framework" not in s or "name" not in s or "reason" not in s:
            raise PlannerError(f"第 {i} 個 suggestion 缺欄位：{s}")
        out.append({
            "framework": int(s["framework"]),
            "name": s["name"],
            "reason": s["reason"],
            "rank": i,
        })
    return out


_STAGE1_TEMPLATE = """你是 Threads 內容結構顧問。以下是 16+1 個文案框架：

{frameworks_md}

使用者題目：{topic}

請挑出最適合這個題目的 3 個框架，依匹配度排序。
輸出純 JSON（不要 markdown code fence）：

{{
  "suggestions": [
    {{"framework": 11, "name": "逆襲引流", "reason": "一句話理由"}}
  ]
}}
"""


def build_stage1_prompt(topic: str, frameworks_md: str) -> str:
    return _STAGE1_TEMPLATE.format(frameworks_md=frameworks_md, topic=topic)


_STAGE2_HEADER = """你是 Threads 串文結構專家。任務：把題目套用指定框架，產出可直接填內容的骨架。

## 題目
{topic}

## 指定框架
{framework_section}
"""

_STAGE2_STYLE_SECTION = """
## 風格範本（使用者過去高互動貼文，模仿語氣與句型，不要抄內容）
{style_posts_rendered}
"""

_STAGE2_OUTPUT_SPEC = """
## 輸出格式要求
- Format: {fmt}
- Thread: 7-10 條，每條 300-500 字；主貼定調、後續遞進
- Single: 1 條 ≤500 字，壓縮完整結構
- **整份 plan.md 總長 ≤3500 字元**（含所有章節；超過請壓縮「內容方向」）

## 輸出 Markdown 結構（照這個格式輸出；關鍵章節必須前置）

# {{題目}}

- 框架：{{編號}} {{名稱}}
- 格式：{fmt}
- 預估總字數：{{數字}}

## 目標受眾
- 誰會想讀：1-2 句具體描述
- 痛點 / 動機：他們為什麼點進來

## 骨架

### 主貼（P1）
- 【鉤子類型】：
- 【字數建議】：
- 【內容方向】：2-3 句指引，**不是成稿**
- 【情緒】：

### P2
...

## 互動設計
- 結尾 CTA 類型（互動式/夥伴式/Slogan/反轉式）：
- 可加的互動元素：

## 風險提示
LLM 自評骨架可能的弱點 1-2 點。
"""


def build_stage2_prompt(
    topic: str,
    framework_section: str,
    style_posts: list[dict],
    fmt: str,
) -> str:
    parts = [_STAGE2_HEADER.format(topic=topic, framework_section=framework_section)]
    if style_posts:
        rendered = []
        for i, p in enumerate(style_posts, start=1):
            rate = p.get("engagement_rate", 0)
            rendered.append(f"[第 {i} 篇] 互動率 {rate}%\n{p.get('full_text', '')}\n---")
        parts.append(_STAGE2_STYLE_SECTION.format(style_posts_rendered="\n".join(rendered)))
    parts.append(_STAGE2_OUTPUT_SPEC.format(fmt=fmt))
    return "".join(parts)


def _call_claude(prompt: str, model: str) -> str:
    """Run `claude -p <prompt> --model <model>`, return stdout.

    Prompt 透過 argv 傳入（對齊 analyzer.py），不用 stdin。
    Windows 沿用 advisor.review_draft 的 shell=True 模式（commit 7ee59e0）。
    TODO(shell-fix): 另開 ticket 把整個專案的 Windows subprocess 改成
    shell=False + claude.cmd 絕對路徑，避免 shell 注入風險。
    Retries once on timeout.
    """
    use_shell = platform.system() == "Windows"
    cmd = ["claude", "-p", prompt, "--model", model]

    last_err: Exception | None = None
    for attempt in range(2):  # 1 次 + 1 次 retry
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=_CLAUDE_TIMEOUT_SEC,
                encoding="utf-8",
                shell=use_shell,
            )
            if result.returncode != 0:
                raise PlannerError(
                    f"claude -p exit {result.returncode}; stderr: {result.stderr[:500]}"
                )
            return result.stdout
        except subprocess.TimeoutExpired as e:
            last_err = e
            logger.warning("claude -p 超時 (attempt %d/2)", attempt + 1)
            continue
    raise PlannerError(f"claude -p 超時 {_CLAUDE_TIMEOUT_SEC}s x2 retries") from last_err


_STAGE1_MODEL = "haiku"


def suggest_frameworks(topic: str, frameworks_md: str) -> list[dict]:
    """只跑 Stage 1：回傳 LLM 建議的框架清單。"""
    prompt = build_stage1_prompt(topic=topic, frameworks_md=frameworks_md)
    stdout = _call_claude(prompt, model=_STAGE1_MODEL)
    return parse_suggestions_json(stdout)


def generate_plan(
    topic: str,
    frameworks_md: str,
    top_posts: list[dict],
    framework: int | str | None,
    fmt: str,
    stage2_model: str,
    auto: bool = False,
    chosen_framework: int | str | None = None,
) -> tuple[str, int]:
    """產生 plan.md。

    Args:
        framework: 若指定，跳過 Stage 1 直接用此框架
        auto: 無 framework 時若 True，取 Stage 1 第一建議；若 False 則 raise（讓 CLI 層做互動）
        chosen_framework: CLI 互動選擇後傳入的框架（覆寫 Stage 1 第一建議）

    Returns:
        (plan_markdown, used_framework_id)
    """
    # 決定最終用哪個框架
    if framework is not None:
        section = extract_framework_section(frameworks_md, framework)
        if section is None:
            raise PlannerError(f"未知框架：{framework}")
        used = _resolve_id(frameworks_md, framework)
    elif chosen_framework is not None:
        section = extract_framework_section(frameworks_md, chosen_framework)
        if section is None:
            raise PlannerError(f"未知框架：{chosen_framework}")
        used = _resolve_id(frameworks_md, chosen_framework)
    else:
        suggestions = suggest_frameworks(topic, frameworks_md)
        if not suggestions:
            raise PlannerError("LLM 未回傳任何框架建議")
        if not auto:
            raise PlannerError("需要互動選擇，但 auto=False；CLI 層應先呼叫 suggest_frameworks")
        pick = suggestions[0]["framework"]
        section = extract_framework_section(frameworks_md, pick)
        if section is None:
            raise PlannerError(f"LLM 建議的框架 {pick} 在 frameworks_md 中不存在")
        used = pick

    # Stage 2
    prompt = build_stage2_prompt(
        topic=topic, framework_section=section, style_posts=top_posts, fmt=fmt,
    )
    plan_md = _call_claude(prompt, model=stage2_model)
    return plan_md, used


def _resolve_id(frameworks_md: str, key: int | str) -> int:
    """解析框架 ID：如果是 int 就直接返回，如果是 str 就查表解析成 ID。"""
    for fw in list_frameworks(frameworks_md):
        if (isinstance(key, int) and fw["id"] == key) or (isinstance(key, str) and fw["name"] == key):
            return fw["id"]
    raise PlannerError(f"無法解析框架 id：{key}")


def resolve_plan_config(config: dict, cli_model: str | None, cli_style_posts: int | None, cli_format: str | None) -> dict:
    """CLI 旗標優先，config.yaml 其次，程式預設最後。"""
    plan_cfg = (config.get("advisor") or {}).get("plan") or {}
    return {
        "stage1_model": plan_cfg.get("stage1_model", "haiku"),
        "stage2_model": cli_model or plan_cfg.get("stage2_model", "sonnet"),
        "style_posts": cli_style_posts if cli_style_posts is not None else plan_cfg.get("default_style_posts", 3),
        "format": cli_format or plan_cfg.get("default_format", "thread"),
    }
