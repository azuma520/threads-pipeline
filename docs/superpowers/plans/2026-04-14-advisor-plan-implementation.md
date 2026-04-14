# advisor plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `advisor plan "題目"` 指令，讓 LLM 基於使用者歷史貼文風格和 16+1 文案框架，產出串文骨架 `plan.md`，接入既有 `advisor review` 流程。

**Architecture:** 兩階段設計——Stage 1 用 haiku 從 16+1 框架挑 3 個候選（或使用者 `--framework` 強制指定），Stage 2 用 sonnet 套用選定框架 + top N 歷史高互動貼文當風格範本，生成 plan.md。所有互動決策點都有對應的非互動旗標（agent-friendly）。

**Tech Stack:** Python 3.13、`claude -p` CLI subprocess、Jinja2、SQLite（既有 `get_top_posts`）、argparse、pytest（mock + LLM-as-judge eval）。

**Spec:** `docs/superpowers/specs/2026-04-14-advisor-plan-design.md`

---

## File Structure

**新增檔案**：
- `threads_pipeline/planner.py` — 核心模組（slug、框架切章節、prompt 組裝、LLM 呼叫、plan 產生）
- `tests/test_planner.py` — 單元 + 整合測試
- `tests/evals/__init__.py` — eval 測試 package
- `tests/evals/conftest.py` — eval pytest_addoption（註：必須在 conftest.py，不能寫在 test 檔）
- `tests/evals/test_plan_quality.py` — LLM-as-judge 品質評分（Layer 3）

**⚠️ 決策變更 vs. spec §3**：原 spec 列 `templates/plan_output.md.j2` Jinja2 模板，本計畫**取消該模板**。最終 plan.md 直接由 LLM 依 Stage 2 prompt 內嵌的 Markdown 骨架輸出，不經 Jinja2 render。理由：（1）LLM 已被要求「照這個格式輸出」，再經 Jinja2 會重複；（2）骨架內容是 LLM 動態產生，Jinja2 的值本來就要從 LLM 回覆解析——多一層意義不大。Spec §3 結案後補同步。

**修改檔案**：
- `threads_pipeline/advisor.py`：
  - 第 211 行 `plan_content[:2000]` → `plan_content[:4000]`
  - 新增 `plan`、`list-frameworks` 子 parser 與 `_cmd_plan()` / `_cmd_list_frameworks()`
- `threads_pipeline/config.yaml`：新增 `advisor.plan.stage2_model: sonnet`
- `CLAUDE.md`：補 `advisor plan` 指令範例

**不動**：
- `references/copywriting-frameworks.md`（被 planner 讀取的資料源）
- `threads_pipeline/analyzer.py`（subprocess 呼叫風格參考來源，不改）
- `threads_pipeline/db_helpers.py`（`get_top_posts` 直接用）

---

## Task 0: Prep — review 截斷放寬 + .gitignore

獨立的小改動先落地。

**Files:**
- Modify: `threads_pipeline/advisor.py:211`
- Modify: `.gitignore`
- Test: `tests/test_advisor.py`

- [ ] **Step 1: Write failing test for new review truncation**

Append to `tests/test_advisor.py`:

```python
def test_review_prompt_plan_truncation_is_4000():
    from threads_pipeline.advisor import _build_review_prompt
    long_plan = "P" * 5000
    prompt = _build_review_prompt(draft="draft", analysis_json={}, plan_content=long_plan)
    assert "P" * 4000 in prompt
    assert "P" * 4001 not in prompt
```

- [ ] **Step 2: Run, verify fail**

Run: `cd "c:/Users/user/OneDrive/桌面/threads_pipeline/.." && PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_advisor.py::test_review_prompt_plan_truncation_is_4000 -v`
Expected: FAIL — current limit 2000.

- [ ] **Step 3: Change the limit**

Edit `threads_pipeline/advisor.py` around line 202:

Find: `plan_section = f"## 發文規劃\n{plan_content[:2000]}"`
Replace: `plan_section = f"## 發文規劃\n{plan_content[:4000]}"`

- [ ] **Step 4: Run, verify pass + full regression**

Run: `PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_advisor.py -v`
Expected: ALL pass.

- [ ] **Step 5: Add drafts ignore**

Check current `.gitignore`:
```bash
cd "c:/Users/user/OneDrive/桌面/threads_pipeline" && grep -E "^drafts" .gitignore 2>&1 || echo "missing"
```

If missing, append to `.gitignore`:
```
# advisor plan / review artifacts
drafts/*.plan.md
drafts/*.review.md
```
（不 ignore 整個 `drafts/`，使用者手寫 `*.txt`/`*.md` 草稿仍可追蹤。）

- [ ] **Step 6: Commit**

```bash
cd "c:/Users/user/OneDrive/桌面/threads_pipeline"
git add threads_pipeline/advisor.py tests/test_advisor.py .gitignore
git commit -m "chore: raise review plan truncation to 4000 + ignore drafts/*.plan.md

Preps for advisor plan command. Uses full 3500-char plan.md without chop."
```

---

## Task 1: planner.py — slugify()

**Files:**
- Create: `threads_pipeline/planner.py`
- Test: `tests/test_planner.py`

- [ ] **Step 1: Write failing test for slugify**

Create `tests/test_planner.py`:

```python
"""planner 測試。"""

import pytest


class TestSlugify:
    def test_chinese_only(self):
        from threads_pipeline.planner import slugify
        # 原始 21 字會被 20 字上限截掉最後「得」
        assert slugify("我學 Claude Code 一個月的心得") == "我學-claude-code-一個月的心"

    def test_strips_illegal_chars(self):
        from threads_pipeline.planner import slugify
        # Windows 檔名不合法字元
        assert slugify('題目/含*特殊?字元"<>|') == "題目含特殊字元"

    def test_truncates_over_20_chars(self):
        from threads_pipeline.planner import slugify
        topic = "這是一個超過二十個字元的非常冗長的題目用來測試截斷行為是否正確"
        result = slugify(topic)
        assert len(result) <= 20

    def test_lowercases_english(self):
        from threads_pipeline.planner import slugify
        assert "claude-code" in slugify("Claude Code")

    def test_empty_or_all_special_returns_timestamp_slug(self, monkeypatch):
        from threads_pipeline import planner
        class _DT:
            @staticmethod
            def now(tz=None):
                import datetime
                return datetime.datetime(2026, 4, 14, 10, 30, tzinfo=datetime.timezone.utc)
        monkeypatch.setattr(planner, "datetime", _DT)
        assert planner.slugify("///***???") == "plan-20260414-1030"
        assert planner.slugify("") == "plan-20260414-1030"

    def test_multiple_spaces_collapse(self):
        from threads_pipeline.planner import slugify
        assert slugify("hello    world") == "hello-world"
```

- [ ] **Step 2: Run test, verify fail**

Run: `cd "c:/Users/user/OneDrive/桌面/threads_pipeline/.." && PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_planner.py::TestSlugify -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'threads_pipeline.planner'`

- [ ] **Step 3: Implement slugify**

Create `threads_pipeline/planner.py`:

```python
"""advisor plan 串文骨架生成器。"""

from __future__ import annotations

import re
from datetime import datetime, timezone

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
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd "c:/Users/user/OneDrive/桌面/threads_pipeline/.." && PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_planner.py::TestSlugify -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
cd "c:/Users/user/OneDrive/桌面/threads_pipeline"
git add threads_pipeline/planner.py tests/test_planner.py
git commit -m "feat(planner): slugify for plan filename"
```

---

## Task 2: planner.py — extract_framework_section()

**Files:**
- Modify: `threads_pipeline/planner.py`
- Test: `tests/test_planner.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_planner.py`:

```python
class TestExtractFrameworkSection:
    @pytest.fixture
    def sample_md(self):
        return """# 爆款文案腳本 16+1 結構

## 結構總覽

| # | 名稱 | 公式 | 適用場景 |
|---|------|-----|---------|
| 01 | 引爆行動 | 觀點 → 危害 → 論據 → 結論 | 想改變讀者行為 |
| 11 | 逆襲引流 | 積極結果 → 獲得感 → 方案 → 互動結尾 | 分享成功經驗 |
| 15 | 通用類 | 鉤子開頭 → 塑造期待 → 解決方案 → 結尾 | 萬用結構 |

## 4 類結尾
| 類型 | 特點 |
|------|------|
| 互動式 | 引導留言 |
"""

    def test_extract_by_id(self, sample_md):
        from threads_pipeline.planner import extract_framework_section
        out = extract_framework_section(sample_md, 11)
        assert "逆襲引流" in out
        assert "積極結果" in out
        assert "分享成功經驗" in out

    def test_extract_by_name(self, sample_md):
        from threads_pipeline.planner import extract_framework_section
        out = extract_framework_section(sample_md, "逆襲引流")
        assert "11" in out
        assert "積極結果" in out

    def test_unknown_returns_none(self, sample_md):
        from threads_pipeline.planner import extract_framework_section
        assert extract_framework_section(sample_md, 99) is None
        assert extract_framework_section(sample_md, "不存在") is None

    def test_list_all_frameworks(self, sample_md):
        from threads_pipeline.planner import list_frameworks
        result = list_frameworks(sample_md)
        assert len(result) == 3
        ids = [fw["id"] for fw in result]
        assert 1 in ids and 11 in ids and 15 in ids
        fw11 = next(fw for fw in result if fw["id"] == 11)
        assert fw11["name"] == "逆襲引流"
        assert "積極結果" in fw11["formula"]
        assert "分享成功經驗" in fw11["when_to_use"]
```

- [ ] **Step 2: Run, verify fail**

Run: `cd "c:/Users/user/OneDrive/桌面/threads_pipeline/.." && PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_planner.py::TestExtractFrameworkSection -v`
Expected: FAIL — import error

- [ ] **Step 3: Implement**

Append to `threads_pipeline/planner.py`:

```python
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
```

- [ ] **Step 4: Run, verify pass**

Run: `cd "c:/Users/user/OneDrive/桌面/threads_pipeline/.." && PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_planner.py::TestExtractFrameworkSection -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Verify against real frameworks file**

Run: `cd "c:/Users/user/OneDrive/桌面/threads_pipeline/.." && PYTHONUTF8=1 python -c "from threads_pipeline.planner import list_frameworks; md = open(r'c:/Users/user/OneDrive/桌面/threads_pipeline/references/copywriting-frameworks.md', encoding='utf-8').read(); fws = list_frameworks(md); print(f'Found {len(fws)} frameworks'); [print(f' {fw[\"id\"]:02d} {fw[\"name\"]}') for fw in fws]"`
Expected: `Found 16 frameworks` and list 01–16

Note: the `+1` in "16+1" refers to the 4 結尾類型 (not a 17th framework) — spec text "17 個框架" is corrected to 16 structure frameworks + 4 ending types.

- [ ] **Step 6: Commit**

```bash
git add threads_pipeline/planner.py tests/test_planner.py
git commit -m "feat(planner): framework markdown parsing (list + extract)"
```

---

## Task 3: planner.py — parse_suggestions_json()

- [ ] **Step 1: Write failing test**

Append to `tests/test_planner.py`:

```python
class TestParseSuggestionsJson:
    def test_valid(self):
        from threads_pipeline.planner import parse_suggestions_json
        stdout = '{"suggestions": [{"framework": 11, "name": "逆襲引流", "reason": "好"}]}'
        result = parse_suggestions_json(stdout)
        assert len(result) == 1
        assert result[0]["framework"] == 11
        assert result[0]["rank"] == 1

    def test_multiple_ranked(self):
        from threads_pipeline.planner import parse_suggestions_json
        stdout = '{"suggestions": [{"framework": 11, "name": "A", "reason": "r1"}, {"framework": 7, "name": "B", "reason": "r2"}]}'
        result = parse_suggestions_json(stdout)
        assert [s["rank"] for s in result] == [1, 2]

    def test_invalid_json_raises(self):
        from threads_pipeline.planner import parse_suggestions_json, PlannerError
        with pytest.raises(PlannerError, match="解析"):
            parse_suggestions_json("not json")

    def test_missing_suggestions_key_raises(self):
        from threads_pipeline.planner import parse_suggestions_json, PlannerError
        with pytest.raises(PlannerError):
            parse_suggestions_json('{"foo": []}')

    def test_missing_framework_field_raises(self):
        from threads_pipeline.planner import parse_suggestions_json, PlannerError
        with pytest.raises(PlannerError):
            parse_suggestions_json('{"suggestions": [{"name": "x"}]}')

    def test_strips_markdown_code_fence(self):
        from threads_pipeline.planner import parse_suggestions_json
        stdout = '```json\n{"suggestions": [{"framework": 11, "name": "A", "reason": "r"}]}\n```'
        result = parse_suggestions_json(stdout)
        assert result[0]["framework"] == 11
```

- [ ] **Step 2: Run, verify fail**

Run: `PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_planner.py::TestParseSuggestionsJson -v`
Expected: FAIL

- [ ] **Step 3: Implement**

Append to `threads_pipeline/planner.py`:

```python
import json


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
```

- [ ] **Step 4: Run, verify pass**

Run: `PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_planner.py::TestParseSuggestionsJson -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add threads_pipeline/planner.py tests/test_planner.py
git commit -m "feat(planner): parse Stage 1 suggestions JSON (no fallback)"
```

---

## Task 4: planner.py — prompt builders

- [ ] **Step 1: Write failing tests**

Append to `tests/test_planner.py`:

```python
class TestPromptBuilders:
    def test_stage1_includes_full_frameworks_md(self):
        from threads_pipeline.planner import build_stage1_prompt
        fws_md = "## 結構總覽 ..."
        topic = "我的題目"
        prompt = build_stage1_prompt(topic=topic, frameworks_md=fws_md)
        assert fws_md in prompt
        assert topic in prompt
        assert "JSON" in prompt
        assert "suggestions" in prompt

    def test_stage2_includes_framework_and_style(self):
        from threads_pipeline.planner import build_stage2_prompt
        prompt = build_stage2_prompt(
            topic="題目",
            framework_section="編號：11\n名稱：逆襲引流",
            style_posts=[{"full_text": "貼文一", "engagement_rate": 3.5}],
            fmt="thread",
        )
        assert "題目" in prompt
        assert "逆襲引流" in prompt
        assert "貼文一" in prompt
        assert "thread" in prompt
        assert "3500" in prompt  # total length cap
        assert "目標受眾" in prompt  # required section

    def test_stage2_single_format(self):
        from threads_pipeline.planner import build_stage2_prompt
        prompt = build_stage2_prompt(
            topic="t", framework_section="fs", style_posts=[], fmt="single"
        )
        assert "single" in prompt
        assert "500 字" in prompt

    def test_stage2_no_style_posts_removes_section(self):
        """0 篇風格範本 → prompt 中完整移除「風格範本」段落，不留空標題。"""
        from threads_pipeline.planner import build_stage2_prompt
        prompt = build_stage2_prompt(
            topic="t", framework_section="fs", style_posts=[], fmt="thread"
        )
        assert "風格範本" not in prompt

    def test_stage2_with_style_posts_includes_section(self):
        from threads_pipeline.planner import build_stage2_prompt
        prompt = build_stage2_prompt(
            topic="t", framework_section="fs",
            style_posts=[{"full_text": "貼文A", "engagement_rate": 4.1}], fmt="thread"
        )
        assert "## 風格範本" in prompt
        assert "貼文A" in prompt
```

- [ ] **Step 2: Run, verify fail**

Run: `PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_planner.py::TestPromptBuilders -v`
Expected: FAIL

- [ ] **Step 3: Implement prompts**

Append to `threads_pipeline/planner.py`:

```python
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
```

- [ ] **Step 4: Run, verify pass**

Run: `PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_planner.py::TestPromptBuilders -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add threads_pipeline/planner.py tests/test_planner.py
git commit -m "feat(planner): Stage 1 and Stage 2 prompt builders"
```

---

## Task 5: planner.py — _call_claude() subprocess wrapper

**⚠️ Subprocess 介面對齊**：這個模組必須對齊 `analyzer.py` 的 `claude -p` 呼叫模式（argv 傳 prompt，不是 stdin）。參考 `analyzer.py` 的 `subprocess.run(["claude", "-p", prompt, "--model", "haiku"], ...)`。Windows `shell=use_shell` 處理參考 `advisor.review_draft`（`advisor.py:234-246`）。

> 注：既有 `advisor.review_draft` 的 `shell=True` + list cmd 在 Windows 屬舊 bug（commit 7ee59e0 部分修過）。為了一致，本模組同樣使用 `shell=use_shell`——留 `TODO(shell-fix)`，待另開 ticket 統一把整個專案的 Windows subprocess 改成 `shell=False` + `claude.cmd` 絕對路徑。

- [ ] **Step 1: Write failing test (mock subprocess.run)**

Append to `tests/test_planner.py`:

```python
from unittest.mock import patch, MagicMock


class TestCallClaude:
    def test_success_prompt_in_argv(self):
        """prompt 透過 argv 傳入（對齊 analyzer.py），非 stdin。"""
        from threads_pipeline.planner import _call_claude
        with patch("threads_pipeline.planner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="result", stderr="")
            out = _call_claude("prompt text", model="haiku")
            assert out == "result"
            args, kwargs = mock_run.call_args
            cmd = args[0]
            assert cmd[0] == "claude"
            assert cmd[1] == "-p"
            assert cmd[2] == "prompt text"  # argv #2 = prompt
            assert "--model" in cmd
            assert "haiku" in cmd
            assert kwargs.get("input") is None  # NOT stdin
            assert kwargs["encoding"] == "utf-8"
            assert kwargs["timeout"] == 60

    def test_nonzero_exit_raises(self):
        from threads_pipeline.planner import _call_claude, PlannerError
        with patch("threads_pipeline.planner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="boom")
            with pytest.raises(PlannerError, match="claude"):
                _call_claude("p", model="haiku")

    def test_timeout_retries_once_then_raises(self):
        import subprocess
        from threads_pipeline.planner import _call_claude, PlannerError
        with patch("threads_pipeline.planner.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=60)
            with pytest.raises(PlannerError, match="超時"):
                _call_claude("p", model="haiku")
            assert mock_run.call_count == 2  # 1 次 + 1 次 retry

    def test_windows_uses_shell(self):
        from threads_pipeline.planner import _call_claude
        with patch("threads_pipeline.planner.platform.system", return_value="Windows"):
            with patch("threads_pipeline.planner.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
                _call_claude("p", model="haiku")
                _, kwargs = mock_run.call_args
                assert kwargs["shell"] is True

    def test_non_windows_no_shell(self):
        from threads_pipeline.planner import _call_claude
        with patch("threads_pipeline.planner.platform.system", return_value="Linux"):
            with patch("threads_pipeline.planner.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
                _call_claude("p", model="haiku")
                _, kwargs = mock_run.call_args
                assert kwargs["shell"] is False
```

- [ ] **Step 2: Run, verify fail**

Run: `PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_planner.py::TestCallClaude -v`
Expected: FAIL — `_call_claude` not defined

- [ ] **Step 3: Implement**

Append to `threads_pipeline/planner.py`:

```python
import platform
import subprocess
import logging

logger = logging.getLogger(__name__)

_CLAUDE_TIMEOUT_SEC = 60


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
```

- [ ] **Step 4: Run, verify pass**

Run: `PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_planner.py::TestCallClaude -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add threads_pipeline/planner.py tests/test_planner.py
git commit -m "feat(planner): _call_claude subprocess wrapper with retry + Windows shell"
```

---

## Task 6: planner.py — generate_plan() orchestration

- [ ] **Step 1: Write failing integration test**

Append to `tests/test_planner.py`:

```python
class TestGeneratePlan:
    @pytest.fixture
    def frameworks_md(self):
        return (
            "## 結構總覽\n"
            "| # | 名稱 | 公式 | 適用場景 |\n"
            "|---|------|-----|---------|\n"
            "| 11 | 逆襲引流 | 積極結果 → 獲得感 | 分享成功經驗 |\n"
            "| 15 | 通用類 | 鉤子開頭 → 結尾 | 萬用結構 |\n"
        )

    def test_full_flow_with_framework_forced(self, frameworks_md):
        """給 --framework 時跳過 Stage 1，只呼叫 Stage 2。"""
        from threads_pipeline.planner import generate_plan
        with patch("threads_pipeline.planner._call_claude") as mock_call:
            mock_call.return_value = "# 題目\n- 框架：11 逆襲引流\n骨架內容"
            plan_md, framework_used = generate_plan(
                topic="題目",
                frameworks_md=frameworks_md,
                top_posts=[{"full_text": "貼文A", "engagement_rate": 3.0}],
                framework=11,
                fmt="thread",
                stage2_model="sonnet",
            )
            assert "骨架內容" in plan_md
            assert framework_used == 11
            assert mock_call.call_count == 1
            _, kwargs = mock_call.call_args
            assert kwargs["model"] == "sonnet"

    def test_full_flow_auto_picks_first_suggestion(self, frameworks_md):
        """無 framework 時 Stage 1 挑 + 用 auto 模式取第一個建議。"""
        from threads_pipeline.planner import generate_plan
        with patch("threads_pipeline.planner._call_claude") as mock_call:
            mock_call.side_effect = [
                '{"suggestions": [{"framework": 11, "name": "逆襲引流", "reason": "好"}]}',
                "# 題目\n骨架",
            ]
            plan_md, framework_used = generate_plan(
                topic="題目", frameworks_md=frameworks_md, top_posts=[],
                framework=None, fmt="thread", stage2_model="sonnet",
                auto=True,
            )
            assert framework_used == 11
            assert mock_call.call_count == 2

    def test_stage1_json_fail_raises(self, frameworks_md):
        from threads_pipeline.planner import generate_plan, PlannerError
        with patch("threads_pipeline.planner._call_claude") as mock_call:
            mock_call.return_value = "not json"
            with pytest.raises(PlannerError, match="JSON"):
                generate_plan(
                    topic="題目", frameworks_md=frameworks_md, top_posts=[],
                    framework=None, fmt="thread", stage2_model="sonnet", auto=True,
                )

    def test_unknown_framework_raises(self, frameworks_md):
        from threads_pipeline.planner import generate_plan, PlannerError
        with pytest.raises(PlannerError, match="框架"):
            generate_plan(
                topic="題目", frameworks_md=frameworks_md, top_posts=[],
                framework=99, fmt="thread", stage2_model="sonnet",
            )

    def test_suggest_only_returns_suggestions(self, frameworks_md):
        """`--suggest-only` 模式：只跑 Stage 1，回傳 suggestions list，不生 plan。"""
        from threads_pipeline.planner import suggest_frameworks
        with patch("threads_pipeline.planner._call_claude") as mock_call:
            mock_call.return_value = '{"suggestions": [{"framework": 11, "name": "逆襲引流", "reason": "好"}]}'
            out = suggest_frameworks(topic="題目", frameworks_md=frameworks_md)
            assert out[0]["framework"] == 11
            assert out[0]["rank"] == 1
            assert mock_call.call_count == 1
```

- [ ] **Step 2: Run, verify fail**

Run: `PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_planner.py::TestGeneratePlan -v`
Expected: FAIL

- [ ] **Step 3: Implement orchestration**

Append to `threads_pipeline/planner.py`:

```python
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
        used = pick

    # Stage 2
    prompt = build_stage2_prompt(
        topic=topic, framework_section=section, style_posts=top_posts, fmt=fmt,
    )
    plan_md = _call_claude(prompt, model=stage2_model)
    return plan_md, used


def _resolve_id(frameworks_md: str, key: int | str) -> int:
    for fw in list_frameworks(frameworks_md):
        if (isinstance(key, int) and fw["id"] == key) or (isinstance(key, str) and fw["name"] == key):
            return fw["id"]
    raise PlannerError(f"無法解析框架 id：{key}")
```

- [ ] **Step 4: Run, verify pass**

Run: `PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_planner.py -v`
Expected: ALL tests pass

- [ ] **Step 5: Commit**

```bash
git add threads_pipeline/planner.py tests/test_planner.py
git commit -m "feat(planner): generate_plan orchestration + suggest_frameworks"
```

---

## Task 7: config.yaml — advisor.plan.stage2_model

**Files:**
- Modify: `threads_pipeline/config.yaml`

- [ ] **Step 1: Read current config**

Run: `cat threads_pipeline/config.yaml`

- [ ] **Step 2: Add plan config block**

Edit `threads_pipeline/config.yaml` — append at end (or find `advisor:` block if exists):

```yaml
advisor:
  plan:
    stage2_model: sonnet  # Stage 2 骨架生成模型；可被 CLI --model 覆寫
    stage1_model: haiku   # Stage 1 框架選擇模型（分類任務）
    default_style_posts: 3
    default_format: thread
```

If `advisor:` already exists, merge `plan:` under it.

- [ ] **Step 3: Add config reader helper**

Append to `threads_pipeline/planner.py`:

```python
def resolve_plan_config(config: dict, cli_model: str | None, cli_style_posts: int | None, cli_format: str | None) -> dict:
    """CLI 旗標優先，config.yaml 其次，程式預設最後。"""
    plan_cfg = (config.get("advisor") or {}).get("plan") or {}
    return {
        "stage1_model": plan_cfg.get("stage1_model", "haiku"),
        "stage2_model": cli_model or plan_cfg.get("stage2_model", "sonnet"),
        "style_posts": cli_style_posts if cli_style_posts is not None else plan_cfg.get("default_style_posts", 3),
        "format": cli_format or plan_cfg.get("default_format", "thread"),
    }
```

- [ ] **Step 4: Write test**

Append to `tests/test_planner.py`:

```python
class TestResolvePlanConfig:
    def test_cli_wins(self):
        from threads_pipeline.planner import resolve_plan_config
        out = resolve_plan_config(
            config={"advisor": {"plan": {"stage2_model": "sonnet", "default_style_posts": 5}}},
            cli_model="haiku", cli_style_posts=1, cli_format="single",
        )
        assert out["stage2_model"] == "haiku"
        assert out["style_posts"] == 1
        assert out["format"] == "single"

    def test_config_used_when_no_cli(self):
        from threads_pipeline.planner import resolve_plan_config
        out = resolve_plan_config(
            config={"advisor": {"plan": {"stage2_model": "opus", "default_style_posts": 7}}},
            cli_model=None, cli_style_posts=None, cli_format=None,
        )
        assert out["stage2_model"] == "opus"
        assert out["style_posts"] == 7
        assert out["format"] == "thread"

    def test_defaults_when_no_config(self):
        from threads_pipeline.planner import resolve_plan_config
        out = resolve_plan_config(config={}, cli_model=None, cli_style_posts=None, cli_format=None)
        assert out["stage2_model"] == "sonnet"
        assert out["style_posts"] == 3
        assert out["format"] == "thread"
```

- [ ] **Step 5: Run tests**

Run: `PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_planner.py::TestResolvePlanConfig -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add threads_pipeline/config.yaml threads_pipeline/planner.py tests/test_planner.py
git commit -m "feat(planner): config.yaml advisor.plan block + resolve_plan_config"
```

---

## Task 8: advisor.py — add `plan` subcommand

**Files:**
- Modify: `threads_pipeline/advisor.py`
- Test: `tests/test_advisor.py`

This is the largest task. Two commits: one for CLI plumbing (no interactive loop), one for interactive flow.

### 8a: CLI plumbing, non-interactive (`--auto` / `--framework` / `--suggest-only`)

- [ ] **Step 1: Write failing tests for non-interactive paths**

Append to `tests/test_advisor.py`:

```python
from unittest.mock import patch, MagicMock


def _fake_config():
    return {"advisor": {"plan": {"stage2_model": "sonnet", "stage1_model": "haiku"}}}


class TestCmdPlanNonInteractive:
    @pytest.fixture
    def fake_env(self, tmp_path, sample_db, monkeypatch):
        """Patch config loader, DB path, frameworks md, and drafts dir."""
        fake_fw_md = tmp_path / "frameworks.md"
        fake_fw_md.write_text(
            "## 結構總覽\n| # | 名稱 | 公式 | 適用場景 |\n|---|------|-----|---------|\n"
            "| 11 | 逆襲引流 | A → B | 分享成功經驗 |\n",
            encoding="utf-8",
        )
        drafts_dir = tmp_path / "drafts"
        drafts_dir.mkdir()

        monkeypatch.setattr(
            "threads_pipeline.advisor.load_config", lambda: {
                "storage": {"sqlite_path": str(sample_db)},
                "advisor": {"plan": {"stage2_model": "sonnet", "stage1_model": "haiku"}},
            },
        )
        monkeypatch.setattr(
            "threads_pipeline.advisor.FRAMEWORKS_MD_PATH", str(fake_fw_md)
        )
        monkeypatch.setattr(
            "threads_pipeline.advisor.DRAFTS_DIR", str(drafts_dir)
        )
        return {"drafts": drafts_dir}

    def test_plan_with_framework_writes_file(self, fake_env):
        from threads_pipeline.advisor import _cmd_plan
        import argparse
        args = argparse.Namespace(
            topic="我學 Claude Code 一個月",
            topic_file=None, framework=11, auto=False, format=None, style_posts=None,
            model=None, suggest_only=False, json=False, overwrite=True, no_overwrite=False,
        )
        with patch("threads_pipeline.planner._call_claude", return_value="# 骨架內容"):
            rc = _cmd_plan(args)
        assert rc == 0
        files = list(fake_env["drafts"].glob("*.plan.md"))
        assert len(files) == 1
        assert "骨架內容" in files[0].read_text(encoding="utf-8")

    def test_plan_auto_uses_stage1_first_suggestion(self, fake_env):
        from threads_pipeline.advisor import _cmd_plan
        import argparse
        args = argparse.Namespace(
            topic="題目", topic_file=None, framework=None, auto=True, format=None,
            style_posts=None, model=None, suggest_only=False, json=False,
            overwrite=True, no_overwrite=False,
        )
        with patch("threads_pipeline.planner._call_claude") as mock_call:
            mock_call.side_effect = [
                '{"suggestions":[{"framework":11,"name":"逆襲引流","reason":"好"}]}',
                "# 骨架",
            ]
            rc = _cmd_plan(args)
        assert rc == 0

    def test_plan_suggest_only_json_goes_to_stdout(self, fake_env, capsys):
        from threads_pipeline.advisor import _cmd_plan
        import argparse, json as _json
        args = argparse.Namespace(
            topic="題目", topic_file=None, framework=None, auto=False, format=None,
            style_posts=None, model=None, suggest_only=True, json=True,
            overwrite=False, no_overwrite=False,
        )
        with patch("threads_pipeline.planner._call_claude",
                   return_value='{"suggestions":[{"framework":11,"name":"逆襲引流","reason":"好"}]}'):
            rc = _cmd_plan(args)
        assert rc == 0
        captured = capsys.readouterr()
        data = _json.loads(captured.out)
        assert data["suggestions"][0]["framework"] == 11

    def test_plan_json_parse_fail_exits_3(self, fake_env):
        from threads_pipeline.advisor import _cmd_plan
        import argparse
        args = argparse.Namespace(
            topic="題目", topic_file=None, framework=None, auto=True, format=None,
            style_posts=None, model=None, suggest_only=False, json=False,
            overwrite=True, no_overwrite=False,
        )
        with patch("threads_pipeline.planner._call_claude", return_value="not json"):
            rc = _cmd_plan(args)
        assert rc == 3

    def test_plan_unknown_framework_exits_1(self, fake_env):
        from threads_pipeline.advisor import _cmd_plan
        import argparse
        args = argparse.Namespace(
            topic="題目", topic_file=None, framework=99, auto=False, format=None,
            style_posts=None, model=None, suggest_only=False, json=False,
            overwrite=True, no_overwrite=False,
        )
        rc = _cmd_plan(args)
        assert rc == 1

    def test_plan_file_exists_no_overwrite_exits_4(self, fake_env):
        from threads_pipeline.advisor import _cmd_plan
        import argparse
        (fake_env["drafts"] / "題目.plan.md").write_text("existing", encoding="utf-8")
        args = argparse.Namespace(
            topic="題目", topic_file=None, framework=11, auto=False, format=None,
            style_posts=None, model=None, suggest_only=False, json=False,
            overwrite=False, no_overwrite=True,
        )
        with patch("threads_pipeline.planner._call_claude", return_value="new"):
            rc = _cmd_plan(args)
        assert rc == 4

    def test_plan_stdout_is_path_only_stderr_has_progress(self, fake_env, capsys):
        """agent-friendly：stdout 只含路徑、stderr 含進度訊息。"""
        from threads_pipeline.advisor import _cmd_plan
        import argparse
        args = argparse.Namespace(
            topic="題目", topic_file=None, framework=11, auto=False, format=None,
            style_posts=None, model=None, suggest_only=False, json=False,
            overwrite=True, no_overwrite=False,
        )
        with patch("threads_pipeline.planner._call_claude", return_value="# 骨架"):
            rc = _cmd_plan(args)
        captured = capsys.readouterr()
        assert rc == 0
        # stdout 最後一行是絕對路徑結尾於 .plan.md
        stdout_lines = [l for l in captured.out.strip().splitlines() if l.strip()]
        assert len(stdout_lines) == 1
        assert stdout_lines[0].endswith(".plan.md")
        # stderr 含「已寫入」或「框架」等進度訊息
        assert "寫入" in captured.err or "框架" in captured.err

    def test_plan_non_tty_auto_fallback(self, fake_env, monkeypatch, capsys):
        """stdin 非 tty 且沒給 --auto / --framework → 自動等同 --auto，stderr 警告。"""
        from threads_pipeline.advisor import _cmd_plan
        import argparse
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)
        args = argparse.Namespace(
            topic="題目", topic_file=None, framework=None, auto=False, format=None,
            style_posts=None, model=None, suggest_only=False, json=False,
            overwrite=True, no_overwrite=False,
        )
        with patch("threads_pipeline.planner._call_claude") as mock_call:
            mock_call.side_effect = [
                '{"suggestions":[{"framework":11,"name":"逆襲引流","reason":"好"}]}',
                "# 骨架",
            ]
            rc = _cmd_plan(args)
        captured = capsys.readouterr()
        assert rc == 0
        assert "非 tty" in captured.err or "auto" in captured.err.lower()

    def test_plan_interactive_q_exits_2(self, fake_env, monkeypatch):
        """使用者互動選 q → 整體 exit code 2（整合測試，補 picker unit test）。"""
        from threads_pipeline.advisor import _cmd_plan
        import argparse
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("builtins.input", lambda _: "q")
        args = argparse.Namespace(
            topic="題目", topic_file=None, framework=None, auto=False, format=None,
            style_posts=None, model=None, suggest_only=False, json=False,
            overwrite=True, no_overwrite=False,
        )
        with patch("threads_pipeline.planner._call_claude",
                   return_value='{"suggestions":[{"framework":11,"name":"A","reason":"r"}]}'):
            rc = _cmd_plan(args)
        assert rc == 2
```

**TDD 注意**：Step 2 先跑測試時，`monkeypatch.setattr("threads_pipeline.advisor.FRAMEWORKS_MD_PATH", ...)` 會 `AttributeError`（因為 Step 3 尚未加該常數）——這是預期的。先忽略 fail 類型，實作 Step 3 後再跑會通過。

- [ ] **Step 2: Run, verify fail**

Run: `PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_advisor.py::TestCmdPlanNonInteractive -v`
Expected: FAIL — `_cmd_plan` not defined

- [ ] **Step 3: Implement `_cmd_plan` + argparse wiring**

Edit `threads_pipeline/advisor.py` — add `import os` at top if missing, then add near top-level constants (after existing `TEMPLATES_DIR`):

```python
# 可被 ADVISOR_* 環境變數覆寫（Layer 3 eval 與使用者自訂用）
FRAMEWORKS_MD_PATH = os.environ.get(
    "ADVISOR_FRAMEWORKS_MD",
    str(Path(__file__).parent.parent / "references" / "copywriting-frameworks.md"),
)
DRAFTS_DIR = os.environ.get(
    "ADVISOR_DRAFTS_DIR",
    str(Path(__file__).parent.parent / "drafts"),
)
```

Modify `main()` in `advisor.py` — after existing review_parser, add:

```python
    # plan
    plan_parser = subparsers.add_parser("plan", help="產生串文骨架 plan.md")
    plan_parser.add_argument("topic", nargs="?", help="題目（引號包起來）")
    plan_parser.add_argument("--topic-file", help="從檔案讀題目（避免 shell 跳脫問題）")
    plan_parser.add_argument("--framework", help="強制指定框架編號或名稱")
    plan_parser.add_argument("--auto", action="store_true", help="跳過互動，用 LLM 第一推薦")
    plan_parser.add_argument("--format", choices=["thread", "single"], help="預設 thread")
    plan_parser.add_argument("--style-posts", type=int, help="風格範本條數，預設 3")
    plan_parser.add_argument("--model", help="覆寫 Stage 2 模型（預設 sonnet）")
    plan_parser.add_argument("--suggest-only", action="store_true", help="只跑 Stage 1 回建議")
    plan_parser.add_argument("--json", action="store_true", help="結果以 JSON 輸出 (stdout)")
    overwrite_group = plan_parser.add_mutually_exclusive_group()
    overwrite_group.add_argument("--overwrite", action="store_true", help="檔案已存在直接覆寫")
    overwrite_group.add_argument("--no-overwrite", action="store_true", help="檔案已存在即報錯")

    # list-frameworks
    list_parser = subparsers.add_parser("list-frameworks", help="列出 16+1 框架")
    list_parser.add_argument("--json", action="store_true")
```

Add dispatch in `main()`:

```python
    elif args.command == "plan":
        sys.exit(_cmd_plan(args))
    elif args.command == "list-frameworks":
        sys.exit(_cmd_list_frameworks(args))
```

Add `import sys` at top if missing.

Implement `_cmd_plan()` — append to `advisor.py` before `if __name__ == "__main__"`:

```python
def _cmd_plan(args) -> int:
    """plan 子指令入口。回傳 exit code（給 main() sys.exit 用）。"""
    from threads_pipeline import planner
    from threads_pipeline.main import _load_dotenv, load_config
    from threads_pipeline.db_helpers import get_readonly_connection, get_top_posts
    import sys as _sys

    _load_dotenv()
    config = load_config()

    # 讀題目
    topic = args.topic
    if args.topic_file:
        topic_path = Path(args.topic_file)
        if not topic_path.exists():
            print(f"✗ 找不到題目檔案：{topic_path}", file=_sys.stderr)
            return 1
        topic = topic_path.read_text(encoding="utf-8").strip()
    if not topic:
        print("✗ 請提供題目（引號字串或 --topic-file）", file=_sys.stderr)
        return 1

    # 讀 frameworks md
    fw_md = Path(FRAMEWORKS_MD_PATH).read_text(encoding="utf-8")

    # 解析 --framework（支援編號或名稱）
    framework_arg: int | str | None = None
    if args.framework:
        try:
            framework_arg = int(args.framework)
        except ValueError:
            framework_arg = args.framework
        section = planner.extract_framework_section(fw_md, framework_arg)
        if section is None:
            print(f"✗ 未知框架：{args.framework}", file=_sys.stderr)
            print("合法選項：", file=_sys.stderr)
            for fw in planner.list_frameworks(fw_md):
                print(f"  {fw['id']:02d} {fw['name']}", file=_sys.stderr)
            return 1

    # resolve config
    plan_cfg = planner.resolve_plan_config(
        config, cli_model=args.model, cli_style_posts=args.style_posts, cli_format=args.format,
    )

    # --suggest-only
    if args.suggest_only:
        try:
            suggestions = planner.suggest_frameworks(topic=topic, frameworks_md=fw_md)
        except planner.PlannerError as e:
            print(f"✗ {e}", file=_sys.stderr)
            return 3
        if args.json:
            import json as _json
            print(_json.dumps({"suggestions": suggestions}, ensure_ascii=False))
        else:
            for s in suggestions:
                print(f"[{s['rank']}] {s['framework']:02d} {s['name']}", file=_sys.stderr)
                print(f"    {s['reason']}", file=_sys.stderr)
        return 0

    # 讀 top posts
    try:
        conn = get_readonly_connection(config)
    except FileNotFoundError:
        if plan_cfg["style_posts"] > 0:
            print("⚠ 找不到 SQLite，風格範本將為空", file=_sys.stderr)
        top_posts = []
    else:
        raw_posts = get_top_posts(conn, limit=plan_cfg["style_posts"])
        conn.close()
        top_posts = []
        for p in raw_posts:
            views = p.get("views", 0)
            eng = p.get("likes", 0) + p.get("replies", 0) + p.get("reposts", 0) + p.get("quotes", 0)
            rate = round(eng / views * 100, 1) if views > 0 else 0
            top_posts.append({"full_text": p.get("full_text", ""), "engagement_rate": rate})
        if len(top_posts) < plan_cfg["style_posts"]:
            print(f"⚠ top posts 僅 {len(top_posts)} 篇（預期 {plan_cfg['style_posts']}）", file=_sys.stderr)

    # 決定 interactive vs auto
    is_tty = _sys.stdin.isatty()
    chosen_fw: int | str | None = None
    auto = args.auto
    if framework_arg is None and not auto:
        if not is_tty:
            print("⚠ stdin 非 tty，自動等同 --auto", file=_sys.stderr)
            auto = True
        else:
            # 互動（Step 9b 實作）
            chosen_fw = _interactive_pick_framework(topic=topic, frameworks_md=fw_md)
            if chosen_fw is None:
                print("✗ 已取消", file=_sys.stderr)
                return 2

    # 生骨架
    try:
        plan_md, used = planner.generate_plan(
            topic=topic,
            frameworks_md=fw_md,
            top_posts=top_posts,
            framework=framework_arg,
            fmt=plan_cfg["format"],
            stage2_model=plan_cfg["stage2_model"],
            auto=auto,
            chosen_framework=chosen_fw,
        )
    except planner.PlannerError as e:
        msg = str(e)
        print(f"✗ {msg}", file=_sys.stderr)
        if "JSON" in msg or "解析" in msg or "超時" in msg or "claude" in msg:
            return 3
        return 1

    # 寫檔
    slug = planner.slugify(topic)
    drafts_dir = Path(DRAFTS_DIR)
    drafts_dir.mkdir(parents=True, exist_ok=True)
    out_path = drafts_dir / f"{slug}.plan.md"

    if out_path.exists():
        if args.no_overwrite:
            print(f"✗ 檔案已存在：{out_path}（--no-overwrite）", file=_sys.stderr)
            return 4
        if not args.overwrite and is_tty:
            ans = input(f"覆寫 {out_path}？ [y/N] ").strip().lower()
            if ans != "y":
                print("✗ 已取消（檔案未改變）", file=_sys.stderr)
                return 2

    out_path.write_text(plan_md, encoding="utf-8")
    print(f"✓ plan.md 已寫入：{out_path}（框架 {used:02d}）", file=_sys.stderr)
    print(str(out_path))  # stdout: path for agent consumption
    return 0


def _interactive_pick_framework(topic: str, frameworks_md: str) -> int | str | None:
    """暫時用 auto 行為；Task 8b 會替換為真正的互動 UI。"""
    from threads_pipeline import planner
    suggestions = planner.suggest_frameworks(topic=topic, frameworks_md=frameworks_md)
    return suggestions[0]["framework"] if suggestions else None


def _cmd_list_frameworks(args) -> int:
    """list-frameworks 子指令。"""
    from threads_pipeline import planner
    import sys as _sys

    fw_md = Path(FRAMEWORKS_MD_PATH).read_text(encoding="utf-8")
    frameworks = planner.list_frameworks(fw_md)
    if args.json:
        import json as _json
        print(_json.dumps(frameworks, ensure_ascii=False, indent=2))
    else:
        for fw in frameworks:
            print(f"{fw['id']:02d} {fw['name']}")
            print(f"   公式：{fw['formula']}")
            print(f"   適用：{fw['when_to_use']}")
            print()
    return 0
```

- [ ] **Step 4: Run tests**

Run: `PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_advisor.py::TestCmdPlanNonInteractive -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add threads_pipeline/advisor.py tests/test_advisor.py
git commit -m "feat(advisor): plan + list-frameworks subcommands (non-interactive paths)"
```

### 8b: Interactive framework picker (`[1/2/3/a/q]`)

- [ ] **Step 1: Write failing test**

Append to `tests/test_advisor.py`:

```python
class TestInteractivePicker:
    def test_picks_choice_1(self, monkeypatch):
        from threads_pipeline import advisor
        monkeypatch.setattr("builtins.input", lambda _: "1")
        fw_md = "## 結構總覽\n| # | 名稱 | 公式 | 適用場景 |\n|---|------|-----|---------|\n| 11 | 逆襲引流 | A | 成功經驗 |\n| 7 | PREP | B | 觀點 |\n"
        with patch("threads_pipeline.planner._call_claude",
                   return_value='{"suggestions":[{"framework":11,"name":"逆襲引流","reason":"r1"},{"framework":7,"name":"PREP","reason":"r2"}]}'):
            result = advisor._interactive_pick_framework(topic="t", frameworks_md=fw_md)
        assert result == 11

    def test_picks_choice_2(self, monkeypatch):
        from threads_pipeline import advisor
        monkeypatch.setattr("builtins.input", lambda _: "2")
        fw_md = "## 結構總覽\n| # | 名稱 | 公式 | 適用場景 |\n|---|------|-----|---------|\n| 11 | A | x | y |\n| 7 | B | x | y |\n"
        with patch("threads_pipeline.planner._call_claude",
                   return_value='{"suggestions":[{"framework":11,"name":"A","reason":"r"},{"framework":7,"name":"B","reason":"r"}]}'):
            result = advisor._interactive_pick_framework(topic="t", frameworks_md=fw_md)
        assert result == 7

    def test_q_returns_none(self, monkeypatch):
        from threads_pipeline import advisor
        monkeypatch.setattr("builtins.input", lambda _: "q")
        fw_md = "## 結構總覽\n| # | 名稱 | 公式 | 適用場景 |\n|---|------|-----|---------|\n| 11 | A | x | y |\n"
        with patch("threads_pipeline.planner._call_claude",
                   return_value='{"suggestions":[{"framework":11,"name":"A","reason":"r"}]}'):
            result = advisor._interactive_pick_framework(topic="t", frameworks_md=fw_md)
        assert result is None

    def test_a_lists_then_picks(self, monkeypatch):
        """輸入 a → 列出全部 → 再問一次 → 輸入 1 → 返回第 1 建議。"""
        from threads_pipeline import advisor
        inputs = iter(["a", "1"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        fw_md = "## 結構總覽\n| # | 名稱 | 公式 | 適用場景 |\n|---|------|-----|---------|\n| 11 | A | x | y |\n"
        with patch("threads_pipeline.planner._call_claude",
                   return_value='{"suggestions":[{"framework":11,"name":"A","reason":"r"}]}'):
            result = advisor._interactive_pick_framework(topic="t", frameworks_md=fw_md)
        assert result == 11

    def test_invalid_then_valid(self, monkeypatch):
        """亂輸入 → 再問 → 正確 → 成功。"""
        from threads_pipeline import advisor
        inputs = iter(["99", "foo", "1"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        fw_md = "## 結構總覽\n| # | 名稱 | 公式 | 適用場景 |\n|---|------|-----|---------|\n| 11 | A | x | y |\n"
        with patch("threads_pipeline.planner._call_claude",
                   return_value='{"suggestions":[{"framework":11,"name":"A","reason":"r"}]}'):
            result = advisor._interactive_pick_framework(topic="t", frameworks_md=fw_md)
        assert result == 11
```

- [ ] **Step 2: Run, verify fail**

Run: `PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_advisor.py::TestInteractivePicker -v`
Expected: some pass (auto-returns choice 1 via stub), some fail

- [ ] **Step 3: Replace stub with real interactive picker**

In `advisor.py`, replace `_interactive_pick_framework` with:

```python
def _interactive_pick_framework(topic: str, frameworks_md: str) -> int | str | None:
    """互動詢問使用者選框架。回傳框架 id 或 None（取消）。"""
    from threads_pipeline import planner
    import sys as _sys

    print("正在分析題目適合的結構（claude -p haiku）...", file=_sys.stderr)
    try:
        suggestions = planner.suggest_frameworks(topic=topic, frameworks_md=frameworks_md)
    except planner.PlannerError as e:
        print(f"✗ Stage 1 失敗：{e}", file=_sys.stderr)
        return None

    all_frameworks = planner.list_frameworks(frameworks_md)
    fw_by_id = {fw["id"]: fw for fw in all_frameworks}

    while True:
        print("\nLLM 建議 3 個候選框架：\n", file=_sys.stderr)
        for s in suggestions:
            star = " ★推薦" if s["rank"] == 1 else ""
            fw = fw_by_id.get(s["framework"], {})
            formula = fw.get("formula", "")
            print(f"  [{s['rank']}] {s['framework']:02d} {s['name']}{star}", file=_sys.stderr)
            if formula:
                print(f"      公式：{formula}", file=_sys.stderr)
            print(f"      為什麼：{s['reason']}", file=_sys.stderr)
            print("", file=_sys.stderr)

        ans = input("請選擇 [1/2/3 / a=全部列出 / q=取消]: ").strip().lower()

        if ans == "q":
            return None
        if ans == "a":
            print("\n全部 16+1 框架：\n", file=_sys.stderr)
            for fw in all_frameworks:
                print(f"  {fw['id']:02d} {fw['name']} — {fw['when_to_use']}", file=_sys.stderr)
                print(f"      公式：{fw['formula']}", file=_sys.stderr)
            print("", file=_sys.stderr)
            continue
        if ans in {"1", "2", "3"}:
            idx = int(ans) - 1
            if idx < len(suggestions):
                return suggestions[idx]["framework"]
        print(f"⚠ 無效輸入：{ans}", file=_sys.stderr)
```

- [ ] **Step 4: Run tests**

Run: `PYTHONUTF8=1 python -m pytest threads_pipeline/tests/test_advisor.py::TestInteractivePicker -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Full regression**

Run: `PYTHONUTF8=1 python -m pytest threads_pipeline/tests/ -v`
Expected: ALL tests pass

- [ ] **Step 6: Commit**

```bash
git add threads_pipeline/advisor.py tests/test_advisor.py
git commit -m "feat(advisor): interactive framework picker (1/2/3/a/q)"
```

---

## Task 9: Manual smoke test

**Files:** none (manual verification).

每步驟跑完都要檢查 exit code（PowerShell: `$LASTEXITCODE`；bash: `echo $?`）。

- [ ] **Step 0: Precheck CLI 可用**

Run: `claude --version && python --version`
Expected: 兩者皆顯示版本號，非錯誤。

Run: `ls threads_pipeline/output/threads_insights.db 2>&1 || echo "DB 不存在—將走無風格範本"`

- [ ] **Step 1: list-frameworks**

Run from `桌面/`:
```bash
PYTHONUTF8=1 python -m threads_pipeline.advisor list-frameworks
echo "exit=$?"
```
Expected: 列出 16 個框架；exit=0。

```bash
PYTHONUTF8=1 python -m threads_pipeline.advisor list-frameworks --json | python -c "import sys, json; data = json.load(sys.stdin); print(f'{len(data)} frameworks')"
```
Expected: `16 frameworks`。

- [ ] **Step 2: plan with --framework + --auto**

```bash
PYTHONUTF8=1 python -m threads_pipeline.advisor plan "我學 Claude Code 一個月的心得" --framework 11 --auto --overwrite
echo "exit=$?"
```
Expected:
- stderr: `✓ plan.md 已寫入：...（框架 11）`
- stdout: plan.md 絕對路徑（只有這一行）
- exit=0

驗證：
```bash
cat drafts/我學-claude-code-一個月的心得.plan.md | wc -m  # < 3500
grep -c "## 目標受眾" drafts/我學-claude-code-一個月的心得.plan.md  # = 1
grep -c "## 骨架" drafts/我學-claude-code-一個月的心得.plan.md   # = 1
grep -c "## 互動設計" drafts/我學-claude-code-一個月的心得.plan.md  # = 1
```

- [ ] **Step 3: --suggest-only --json**

```bash
PYTHONUTF8=1 python -m threads_pipeline.advisor plan "給新手的 AI 工具入門指南" --suggest-only --json
echo "exit=$?"
```
Expected: stdout 吐 JSON `{"suggestions": [...]}`（3 個項目、rank 1-3）；exit=0。

- [ ] **Step 4: 互動流程 — 選 1**

**手動操作**（不重導 stdin），實際在 terminal 按鍵：
```bash
PYTHONUTF8=1 python -m threads_pipeline.advisor plan "AI 工具如何改變我的工作流"
```
- 應顯示 3 個候選框架
- 按 `1` 並 Enter
- Expected: exit=0、plan.md 寫入、內容使用 rank 1 的框架

- [ ] **Step 5: 互動流程 — 選 a（列全部）→ 再選 2**

手動重跑 Step 4，這次先按 `a`：
- Expected: 列出 16 個框架全部描述
- 接著再問一次 `請選擇 [1/2/3 / a=全部列出 / q=取消]`
- 按 `2` 並 Enter → 成功寫入 rank 2 框架的 plan

- [ ] **Step 6: 互動流程 — 選 q 取消**

手動重跑，按 `q`：
- Expected: stderr「已取消」、exit=2、**檔案未寫入/未變更**

- [ ] **Step 7: 非 tty 自動 auto**

Pipe 讓 stdin 非 tty：
```bash
echo "" | PYTHONUTF8=1 python -m threads_pipeline.advisor plan "測試非 tty" --overwrite
echo "exit=$?"
```
Expected:
- stderr 出現 `非 tty` 或 `自動等同 --auto` 字樣
- 自動走 auto，不卡輸入
- exit=0

- [ ] **Step 8: review 能吃新 plan.md（4000 字截斷驗證）**

```bash
echo "草稿測試內容" > drafts/smoke-draft.txt
PYTHONUTF8=1 python -m threads_pipeline.advisor review drafts/smoke-draft.txt --plan drafts/我學-claude-code-一個月的心得.plan.md
echo "exit=$?"
```
Expected: review 六維度結果都顯示（特別是**「受眾匹配」維度應該不是「無發文規劃，跳過此維度」**，因為新 plan.md 有「目標受眾」章節）；exit=0。

- [ ] **Step 9: 清理 smoke 產出**

```bash
rm -f drafts/*.plan.md drafts/smoke-draft.txt drafts/*.review.md
```
（`drafts/*.plan.md` 已在 `.gitignore`，但手動清掉讓工作區乾淨。不需要 commit。）

---

## Task 10: Layer 3 eval — LLM-as-judge

**Files:**
- Create: `tests/evals/__init__.py`
- Create: `tests/evals/test_plan_quality.py`
- Create: `tests/evals/golden_topics.json`

- [ ] **Step 1: Create eval folder + conftest + golden topics**

Create `tests/evals/__init__.py` (empty file):
```python
```

Create `tests/evals/conftest.py` (pytest_addoption MUST live in conftest.py or it won't register):
```python
def pytest_addoption(parser):
    parser.addoption(
        "--run-llm-evals",
        action="store_true",
        default=False,
        help="Run Layer 3 LLM-as-judge evals (spends real tokens).",
    )
```

Create `tests/evals/golden_topics.json`:
```json
[
  {
    "topic": "我學 Claude Code 一個月的心得",
    "category": "experience_share",
    "expected_framework_candidates": [11, 14, 3]
  },
  {
    "topic": "給新手的 AI 工具入門指南",
    "category": "teaching",
    "expected_framework_candidates": [16, 5, 8]
  },
  {
    "topic": "為什麼我覺得多數 AI 課程在浪費錢",
    "category": "opinion",
    "expected_framework_candidates": [1, 7, 12]
  }
]
```

- [ ] **Step 2: Create eval script**

Create `tests/evals/test_plan_quality.py`:

```python
"""Layer 3 — LLM-as-judge 品質評分。

不在 CI 跑，作為人工 release gate。
執行：PYTHONUTF8=1 python -m pytest threads_pipeline/tests/evals/ -v --run-llm-evals

pytest_addoption 在 tests/evals/conftest.py（不能寫在此檔，否則不註冊）。
"""

import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path

import pytest

EVAL_DIR = Path(__file__).parent
GOLDEN_TOPICS = json.loads((EVAL_DIR / "golden_topics.json").read_text(encoding="utf-8"))
REPO_ROOT = Path(__file__).parent.parent.parent.parent  # 桌面/

JUDGE_RUBRIC_TEMPLATE = """你是 Threads 內容審查專家。請根據下列 5 個維度，為這份 plan.md 的品質打分（1-5 分）：

1. **框架公式對齊度**：骨架順序是否符合指定框架的公式？
2. **風格一致性**：語氣、句型是否貼近範本貼文？
3. **可執行性**：「內容方向」是否具體到使用者能直接填內容？
4. **格式正確性**：thread 7-10 條 / single ≤500 字規則是否遵守？整份 ≤3500 字？
5. **避免 AI 味**：有沒有誇大象徵、-ing 膚淺分析、破折號過度？

## 指定框架
__FRAMEWORK_INFO__

## 待評分 plan.md
__PLAN_CONTENT__

輸出純 JSON（不要 markdown code fence）：
{
  "scores": {
    "framework_alignment": 1-5,
    "style_consistency": 1-5,
    "actionability": 1-5,
    "format_correctness": 1-5,
    "avoid_ai_smell": 1-5
  },
  "issues": ["..."],
  "pass": true/false
}

任一項 <3 → pass=false。
"""


def _build_judge_prompt(plan_content: str, framework_info: str) -> str:
    """用 str.replace 避免 .format() 被 plan_content / JSON 範例中的 {} 炸掉。"""
    return (
        JUDGE_RUBRIC_TEMPLATE
        .replace("__FRAMEWORK_INFO__", framework_info)
        .replace("__PLAN_CONTENT__", plan_content)
    )


def _run_advisor_plan(topic: str, framework: int, drafts_dir: Path) -> str:
    """真實呼叫 advisor plan，回傳 plan.md 內容。

    透過 ADVISOR_DRAFTS_DIR env 把輸出重導至隔離的 tempdir，避免污染使用者 drafts/。
    env 要 merge os.environ，否則 Windows 會清掉 PATH 找不到 python/claude。
    """
    env = {
        **os.environ,
        "PYTHONUTF8": "1",
        "ADVISOR_DRAFTS_DIR": str(drafts_dir),
    }
    result = subprocess.run(
        ["python", "-m", "threads_pipeline.advisor", "plan", topic,
         "--framework", str(framework), "--auto", "--overwrite"],
        cwd=str(REPO_ROOT),
        capture_output=True, text=True, encoding="utf-8",
        env=env, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"advisor plan failed (rc={result.returncode}):\nstderr: {result.stderr}")
    # stdout 最後一行是 plan.md 絕對路徑
    stdout_lines = [l for l in result.stdout.strip().splitlines() if l.strip()]
    plan_path = Path(stdout_lines[-1])
    return plan_path.read_text(encoding="utf-8")


def _judge_with_subagent(plan_content: str, framework_info: str) -> dict:
    """用 codex CLI 當 judge，回傳評分 JSON。"""
    prompt = _build_judge_prompt(plan_content, framework_info)
    env = {**os.environ, "PYTHONUTF8": "1"}
    result = subprocess.run(
        ["codex", "exec", "-s", "read-only", "-"],
        input=prompt, capture_output=True, text=True, encoding="utf-8",
        timeout=120, shell=platform.system() == "Windows", env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(f"codex judge failed: {result.stderr}")
    text = result.stdout.strip()
    if text.startswith("```"):
        import re
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


@pytest.mark.skipif(
    "not config.getoption('--run-llm-evals', default=False)",
    reason="需 --run-llm-evals 旗標開啟 (成本高)",
)
@pytest.mark.parametrize("topic_spec", GOLDEN_TOPICS, ids=lambda t: t["topic"])
def test_plan_quality(topic_spec, tmp_path):
    topic = topic_spec["topic"]
    fw = topic_spec["expected_framework_candidates"][0]

    plan_md = _run_advisor_plan(topic, fw, drafts_dir=tmp_path)
    judge = _judge_with_subagent(
        plan_content=plan_md,
        framework_info=f"框架 {fw} (候選 {topic_spec['expected_framework_candidates']})",
    )

    print(f"\n== {topic} ==")
    print(json.dumps(judge, ensure_ascii=False, indent=2))

    scores = judge["scores"]
    for key, v in scores.items():
        assert v >= 3, f"{key} = {v} < 3 on topic '{topic}'"
    assert judge.get("pass") is True
```

- [ ] **Step 3: Verify eval is skipped by default**

Run: `PYTHONUTF8=1 python -m pytest threads_pipeline/tests/evals/ -v`
Expected: 3 tests SKIPPED

- [ ] **Step 4: (Optional) Run eval manually**

Only if willing to spend tokens:
```bash
PYTHONUTF8=1 python -m pytest threads_pipeline/tests/evals/ -v --run-llm-evals
```
Expected: 3 tests run; each prints scores; all pass (or collect failures for tuning).

- [ ] **Step 5: Commit**

```bash
git add tests/evals/
git commit -m "test(evals): Layer 3 LLM-as-judge plan quality gate (3 golden topics)"
```

---

## Task 11: CLAUDE.md usage examples

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add plan usage examples**

Edit `CLAUDE.md` — find the `## Commands` section and append under existing advisor commands:

```markdown
# Run advisor plan (from parent directory 桌面/)
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor plan "我學 Claude Code 一個月的心得"
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor plan "題目" --framework 11 --auto --overwrite
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor plan "題目" --suggest-only --json
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor list-frameworks

# Layer 3 品質 eval (成本高，人工 release gate)
$env:PYTHONUTF8=1; python -m pytest threads_pipeline/tests/evals/ --run-llm-evals
```

- [ ] **Step 2: Also update `Project Structure` section**

In `CLAUDE.md` under `## Project Structure`, add `planner.py` to the list:

Find: `├── advisor.py                    # 發文顧問（analyze + review via Codex CLI）`
Append after: `├── planner.py                    # advisor plan 串文骨架生成器（haiku+sonnet 兩階段）`

And under `tests/`:
Append: `│   └── evals/                    # LLM-as-judge 品質評分（Layer 3 release gate）`

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: CLAUDE.md advisor plan usage + project structure"
```

---

## Self-Review Checklist (do before handoff)

1. **Spec coverage** — map spec sections to tasks:
   - §3 架構 (planner.py + advisor.py split) → Tasks 0-8
   - §3 `plan_output.md.j2`：**已取消**（見 Plan 開頭的「⚠️ 決策變更」），待同步 spec §3
   - §4 CLI 介面 → Task 8a (non-interactive) + 8b (interactive)
   - §4 agent-friendly（stdout/stderr 分離、非 tty 自動 auto、exit code 2 整合）→ Task 8a 4 個補強測試
   - §5 Prompt 設計 → Task 4
   - §6 錯誤處理 → Task 8a（所有 exit code 有測試覆蓋）
   - §7 Layer 1/2 → Tasks 1-8 嵌入單元 + 整合測試
   - §7 Layer 3 → Task 10（conftest.py 有 pytest_addoption；eval 透過 ADVISOR_DRAFTS_DIR env 隔離，不污染 drafts/）
   - §8 已決議事項 → Task 7 (config.yaml)
   - §9 落地計畫 → Tasks 0-11

2. **Placeholder scan** — none found (all code blocks contain full code).

3. **Type/signature consistency**:
   - `generate_plan` returns `tuple[str, int]` consistently.
   - `suggestions` dict shape `{framework, name, reason, rank}` used everywhere.
   - `planner.PlannerError` single error class reused.
   - Exit codes in tests match §6 spec table.

4. **Side effects / DB writes** — plan generation is read-only on DB (only `get_top_posts`); writes only to `drafts/`.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-14-advisor-plan-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
