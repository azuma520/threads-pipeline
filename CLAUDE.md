# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A daily pipeline that collects AI/tech trend posts from Meta Threads API, analyzes them with Claude CLI (`claude -p`), tracks account/post insights in SQLite, and generates Markdown reports via Jinja2 templates. Written in Traditional Chinese (繁體中文).

## Commands

```bash
# Run the pipeline
PYTHONUTF8=1 python -m threads_pipeline.main

# Run all tests
python -m pytest

# Run a single test file
python -m pytest tests/test_analyzer.py

# Run a specific test class or method
python -m pytest tests/test_analyzer.py::TestParseAnalysis::test_valid_json
```

## Architecture

The pipeline runs two independent jobs in sequence, each wrapped in its own try/except so one failure doesn't block the other:

**Job A — Trend Collection**: `threads_client.fetch_posts` (keyword search via Threads API with dedup) → `analyzer.analyze_posts` (batch `claude -p` subprocess calls, 50 posts/batch, with fallback on failure) → `report.render_report` (Jinja2 daily report)

**Job B — Insights Tracking**: `insights_tracker.fetch_and_store_post_insights` + `fetch_and_store_account_insights` (Threads insights API → SQLite upsert) → `get_trend` / `get_top_posts` (query SQLite) → `report.render_dashboard` (Jinja2 dashboard report)

### Key design decisions

- **AI analysis uses `claude -p` CLI subprocess**, not the Anthropic SDK. The analyzer shells out to `claude -p <prompt> --model haiku` and parses the JSON response.
- **Config uses `${ENV_VAR}` interpolation** — `main.load_config()` resolves environment variable references in `config.yaml` before YAML parsing. Secrets (like `THREADS_ACCESS_TOKEN`) come from `.env`.
- **SQLite upsert pattern** — `insights_tracker` uses `INSERT ... ON CONFLICT DO UPDATE` with `(collected_date, post_id)` as composite PK for post insights and `collected_date` as PK for account insights.
- **All HTTP requests** go through `threads_client._request_with_retry` with exponential backoff and 429 rate-limit handling.
- The package is imported as `threads_pipeline.*` (e.g., `from threads_pipeline.analyzer import ...`).

## Dependencies

- Python 3.13+
- requests, pyyaml, jinja2
- Claude Code CLI (for `claude -p` in analyzer)
- Meta Threads API access token in `.env`
