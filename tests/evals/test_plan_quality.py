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
