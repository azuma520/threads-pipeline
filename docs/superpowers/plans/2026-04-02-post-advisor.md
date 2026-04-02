# V2.5 貼文健檢（發文顧問）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立發文顧問系統：數據分析（analyze）+ Codex CLI 草稿審查（review），整合演算法知識和 16+1 文案結構框架。

**Architecture:** 新增 `advisor.py`（analyze + review 子指令）和 `db_helpers.py`（共用模組）。Schema 擴充 3 個欄位（full_text, post_hour_local, author_reply_count）。Review 透過 Codex CLI subprocess 做第三方審查。

**Tech Stack:** Python 3.13, SQLite, Codex CLI (v0.115.0), Jinja2

---

## File Structure

### 新增

| 檔案 | 職責 |
|------|------|
| `db_helpers.py` | 共用 config loading、DB 連線、基礎查詢 |
| `advisor.py` | analyze + review 子指令入口 |
| `references/copywriting-frameworks.md` | 16+1 文案結構框架 |
| `templates/advisor_report.md.j2` | 分析報告 Jinja2 模板 |
| `tests/test_db_helpers.py` | db_helpers 測試 |
| `tests/test_advisor.py` | advisor 測試 |

### 修改

| 檔案 | 改動 |
|------|------|
| `insights_tracker.py` | Schema 擴充 + 存新欄位 + import db_helpers |
| `main.py` | import 改為從 db_helpers 取 load_config |
| `.gitignore` | 新增 drafts/ 和 output/advisor/ |

---

### Task 1: Schema 擴充 + insights_tracker 修改

**Files:**
- Modify: `insights_tracker.py`
- Test: `tests/test_advisor.py`（先建空檔）

- [ ] **Step 1: 修改 CREATE_TABLES_SQL 加入新欄位**

在 `insights_tracker.py` 的 `CREATE_TABLES_SQL` 中，修改 `post_insights` 表：

```python
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS post_insights (
    collected_date TEXT NOT NULL,
    post_id        TEXT NOT NULL,
    text_preview   TEXT,
    full_text      TEXT,
    posted_at      TEXT,
    post_hour_local INTEGER,
    username       TEXT,
    views          INTEGER DEFAULT 0,
    likes          INTEGER DEFAULT 0,
    replies        INTEGER DEFAULT 0,
    reposts        INTEGER DEFAULT 0,
    quotes         INTEGER DEFAULT 0,
    author_reply_count INTEGER DEFAULT 0,
    PRIMARY KEY (collected_date, post_id)
);

CREATE TABLE IF NOT EXISTS account_insights (
    collected_date TEXT NOT NULL PRIMARY KEY,
    followers      INTEGER DEFAULT 0,
    total_views    INTEGER DEFAULT 0,
    total_likes    INTEGER DEFAULT 0,
    total_replies  INTEGER DEFAULT 0,
    total_reposts  INTEGER DEFAULT 0
);
"""
```

- [ ] **Step 2: 新增 migrate schema 函式**

在 `insights_tracker.py` 的 `init_db` 函式後新增：

```python
def _migrate_schema(conn: sqlite3.Connection):
    """為已存在的 DB 新增缺少的欄位（向後相容）。"""
    cursor = conn.execute("PRAGMA table_info(post_insights)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    migrations = [
        ("full_text", "TEXT"),
        ("post_hour_local", "INTEGER"),
        ("author_reply_count", "INTEGER DEFAULT 0"),
    ]

    for col_name, col_type in migrations:
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE post_insights ADD COLUMN {col_name} {col_type}")
            logger.info("已新增欄位: %s", col_name)

    conn.commit()
```

並在 `init_db` 中呼叫：

```python
def init_db(config: dict) -> sqlite3.Connection:
    insights_cfg = config.get("insights", {})
    data_dir = Path(insights_cfg.get("data_dir", "./data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / insights_cfg.get("db_name", "threads.db")

    conn = sqlite3.connect(str(db_path))
    conn.executescript(CREATE_TABLES_SQL)
    _migrate_schema(conn)
    return conn
```

- [ ] **Step 3: 修改 UPSERT_POST_SQL 加入新欄位**

```python
UPSERT_POST_SQL = """
INSERT INTO post_insights (collected_date, post_id, text_preview, full_text, posted_at, post_hour_local, username, views, likes, replies, reposts, quotes, author_reply_count)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(collected_date, post_id) DO UPDATE SET
    full_text=excluded.full_text, post_hour_local=excluded.post_hour_local,
    views=excluded.views, likes=excluded.likes, replies=excluded.replies,
    reposts=excluded.reposts, quotes=excluded.quotes,
    author_reply_count=excluded.author_reply_count;
"""
```

- [ ] **Step 4: 新增 _fetch_author_reply_count 函式**

```python
def _fetch_author_reply_count(post_id: str, username: str, token: str) -> int:
    """計算作者在該貼文下回覆了幾則。"""
    url = f"{THREADS_API_BASE}/{post_id}/replies"
    params = {
        "fields": "id,username",
        "access_token": token,
    }
    try:
        data = _request_with_retry(url, params)
        replies = data.get("data", [])
        return sum(1 for r in replies if r.get("username") == username)
    except Exception as e:
        logger.warning("取得貼文 %s 回覆數失敗: %s", post_id, e)
        return 0
```

- [ ] **Step 5: 新增 _calc_post_hour_local 函式**

```python
from zoneinfo import ZoneInfo

def _calc_post_hour_local(posted_at: str, tz_name: str = "Asia/Taipei") -> int | None:
    """將 posted_at 轉換為本地時區的小時數（0-23）。"""
    if not posted_at:
        return None
    try:
        dt = datetime.fromisoformat(posted_at.replace("+0000", "+00:00"))
        tz = ZoneInfo(tz_name)
        return dt.astimezone(tz).hour
    except (ValueError, TypeError):
        return None
```

- [ ] **Step 6: 修改 fetch_and_store_post_insights 使用新欄位**

```python
def fetch_and_store_post_insights(config: dict, conn: sqlite3.Connection) -> int:
    token = config["threads"]["access_token"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tz_name = config.get("insights", {}).get("timezone", "Asia/Taipei")

    posts = _fetch_all_posts(token)
    if not posts:
        print("  無貼文可抓取")
        return 0

    print(f"  取得 {len(posts)} 篇貼文，正在抓取 insights...")

    # 取得自己的 username
    username = posts[0].get("username", "") if posts else ""

    count = 0
    for p in posts:
        post_id = p["id"]
        try:
            insights = _fetch_single_post_insights(post_id, token)
            full_text = p.get("text", "")
            posted_at = p.get("timestamp", "")
            post_hour = _calc_post_hour_local(posted_at, tz_name)
            reply_count = _fetch_author_reply_count(post_id, username, token)

            conn.execute(UPSERT_POST_SQL, (
                today,
                post_id,
                full_text[:50].replace("\n", " "),
                full_text,
                posted_at,
                post_hour,
                p.get("username", ""),
                insights.get("views", 0),
                insights.get("likes", 0),
                insights.get("replies", 0),
                insights.get("reposts", 0),
                insights.get("quotes", 0),
                reply_count,
            ))
            count += 1
        except Exception as e:
            logger.warning("貼文 %s insights 抓取失敗: %s", post_id, e)

    conn.commit()
    return count
```

- [ ] **Step 7: 跑測試確認現有測試不壞**

Run: `python -m pytest -v`
Expected: 全部 PASS

- [ ] **Step 8: Commit**

```bash
git add insights_tracker.py
git commit -m "feat: Schema 擴充 — full_text, post_hour_local, author_reply_count"
```

---

### Task 2: 共用模組 db_helpers.py

**Files:**
- Create: `db_helpers.py`
- Modify: `insights_tracker.py`（import 改用 db_helpers）
- Modify: `main.py`（import 改用 db_helpers）
- Create: `tests/test_db_helpers.py`

- [ ] **Step 1: 建立 tests/test_db_helpers.py 寫測試**

```python
"""db_helpers 測試。"""

import sqlite3
import pytest
from threads_pipeline.db_helpers import get_db_path, get_readonly_connection, get_top_posts, get_trend, get_account_latest


@pytest.fixture
def sample_db(tmp_path):
    """建立含範例數據的測試 DB。"""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE post_insights (
            collected_date TEXT NOT NULL,
            post_id TEXT NOT NULL,
            text_preview TEXT,
            full_text TEXT,
            posted_at TEXT,
            post_hour_local INTEGER,
            username TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            reposts INTEGER DEFAULT 0,
            quotes INTEGER DEFAULT 0,
            author_reply_count INTEGER DEFAULT 0,
            PRIMARY KEY (collected_date, post_id)
        );
        CREATE TABLE account_insights (
            collected_date TEXT NOT NULL PRIMARY KEY,
            followers INTEGER DEFAULT 0,
            total_views INTEGER DEFAULT 0,
            total_likes INTEGER DEFAULT 0,
            total_replies INTEGER DEFAULT 0,
            total_reposts INTEGER DEFAULT 0
        );
        INSERT INTO post_insights VALUES
            ('2026-04-01', 'p1', '高表現AI文', '我是那種很依賴AI學習的人...', '2026-03-06T18:06:00+0000', 18, 'azuma01130626', 61485, 1200, 300, 200, 100, 12),
            ('2026-04-01', 'p2', '低表現教學文', '教學：如何設定環境變數', '2026-03-07T11:00:00+0000', 11, 'azuma01130626', 500, 10, 2, 1, 0, 0),
            ('2026-04-01', 'p3', '中等觀點文', '不知道大家有沒有試過叫AI寫觀察', '2026-03-08T19:28:00+0000', 19, 'azuma01130626', 353, 8, 4, 2, 1, 3);
        INSERT INTO account_insights VALUES
            ('2026-03-31', 205, 5000, 100, 50, 20),
            ('2026-04-01', 206, 5796, 110, 55, 22);
    """)
    conn.commit()
    conn.close()
    return db_path


class TestGetTopPosts:
    def test_returns_sorted_by_views(self, sample_db):
        conn = sqlite3.connect(str(sample_db))
        posts = get_top_posts(conn, limit=3)
        conn.close()
        assert len(posts) == 3
        assert posts[0]["views"] == 61485
        assert posts[0]["full_text"].startswith("我是那種")

    def test_limit(self, sample_db):
        conn = sqlite3.connect(str(sample_db))
        posts = get_top_posts(conn, limit=1)
        conn.close()
        assert len(posts) == 1


class TestGetTrend:
    def test_returns_trend(self, sample_db):
        conn = sqlite3.connect(str(sample_db))
        trend = get_trend(conn)
        conn.close()
        assert trend is not None
        assert trend["followers"]["delta"] == 1

    def test_returns_none_when_insufficient(self, tmp_path):
        db_path = tmp_path / "empty.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE account_insights (collected_date TEXT PRIMARY KEY, followers INTEGER DEFAULT 0, total_views INTEGER DEFAULT 0, total_likes INTEGER DEFAULT 0, total_replies INTEGER DEFAULT 0, total_reposts INTEGER DEFAULT 0)")
        conn.commit()
        trend = get_trend(conn)
        conn.close()
        assert trend is None


class TestGetAccountLatest:
    def test_returns_latest(self, sample_db):
        conn = sqlite3.connect(str(sample_db))
        account = get_account_latest(conn)
        conn.close()
        assert account["followers"] == 206
        assert account["total_views"] == 5796
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_db_helpers.py -v`
Expected: FAIL（db_helpers 不存在）

- [ ] **Step 3: 建立 db_helpers.py**

```python
"""共用資料庫工具：config loading、DB 連線、基礎查詢。"""

import sqlite3
from pathlib import Path


def get_db_path(config: dict) -> Path:
    """從 config 取得 DB 檔案路徑。"""
    insights_cfg = config.get("insights", {})
    data_dir = Path(insights_cfg.get("data_dir", "./data"))
    db_name = insights_cfg.get("db_name", "threads.db")

    # 相對路徑以專案根目錄為基準
    if not data_dir.is_absolute():
        data_dir = Path(__file__).parent / data_dir

    return data_dir / db_name


def get_readonly_connection(config: dict) -> sqlite3.Connection:
    """取得 read-only DB 連線。"""
    db_path = get_db_path(config)
    if not db_path.exists():
        raise FileNotFoundError(f"資料庫不存在: {db_path}")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def get_top_posts(conn: sqlite3.Connection, limit: int = 5) -> list[dict]:
    """取得觀看數最高的 N 篇貼文（最近一次 collected_date）。"""
    rows = conn.execute("""
        SELECT post_id, text_preview, full_text, posted_at, post_hour_local,
               username, views, likes, replies, reposts, quotes, author_reply_count
        FROM post_insights
        WHERE collected_date = (SELECT MAX(collected_date) FROM post_insights)
        ORDER BY views DESC
        LIMIT ?
    """, (limit,)).fetchall()

    cols = ["post_id", "text_preview", "full_text", "posted_at", "post_hour_local",
            "username", "views", "likes", "replies", "reposts", "quotes", "author_reply_count"]
    return [dict(zip(cols, row)) for row in rows]


def get_trend(conn: sqlite3.Connection, days: int = 7) -> dict | None:
    """計算帳號 insights 的 N 天趨勢。數據不足時回傳 None。"""
    rows = conn.execute(
        "SELECT * FROM account_insights ORDER BY collected_date DESC LIMIT ?",
        (days,)
    ).fetchall()

    if len(rows) < 2:
        return None

    cols = [d[0] for d in conn.execute("SELECT * FROM account_insights LIMIT 0").description]
    latest = dict(zip(cols, rows[0]))
    oldest = dict(zip(cols, rows[-1]))

    trend = {}
    for key in ["followers", "total_views"]:
        old_val = oldest.get(key, 0)
        new_val = latest.get(key, 0)
        delta = new_val - old_val
        pct = (delta / old_val * 100) if old_val else 0
        trend[key] = {"value": new_val, "delta": delta, "pct": round(pct, 1)}

    trend["days"] = len(rows)
    return trend


def get_account_latest(conn: sqlite3.Connection) -> dict:
    """取得最新一筆帳號 insights。"""
    row = conn.execute(
        "SELECT * FROM account_insights ORDER BY collected_date DESC LIMIT 1"
    ).fetchone()

    if not row:
        return {}

    cols = [d[0] for d in conn.execute("SELECT * FROM account_insights LIMIT 0").description]
    return dict(zip(cols, row))


def get_post_hour_distribution(conn: sqlite3.Connection, min_views: int = 100) -> dict[int, float]:
    """取得高表現貼文的發文時段分布。回傳 {hour: avg_engagement_rate}。"""
    rows = conn.execute("""
        SELECT post_hour_local, 
               AVG(CASE WHEN views > 0 THEN (likes + replies + reposts + quotes) * 100.0 / views ELSE 0 END) as avg_rate,
               COUNT(*) as count
        FROM post_insights
        WHERE post_hour_local IS NOT NULL
          AND views >= ?
          AND collected_date = (SELECT MAX(collected_date) FROM post_insights)
        GROUP BY post_hour_local
        ORDER BY avg_rate DESC
    """, (min_views,)).fetchall()

    return {row[0]: round(row[1], 1) for row in rows}


def get_engagement_stats(conn: sqlite3.Connection) -> dict:
    """取得整體互動數據統計。"""
    row = conn.execute("""
        SELECT
            AVG(CASE WHEN views > 0 THEN (likes + replies + reposts + quotes) * 100.0 / views ELSE 0 END) as avg_engagement_rate,
            AVG(likes) as avg_likes,
            AVG(replies) as avg_replies,
            AVG(reposts) as avg_reposts,
            AVG(quotes) as avg_quotes,
            AVG(author_reply_count) as avg_author_replies,
            SUM(likes) as total_likes,
            SUM(replies) as total_replies,
            SUM(reposts) as total_reposts,
            COUNT(*) as post_count
        FROM post_insights
        WHERE collected_date = (SELECT MAX(collected_date) FROM post_insights)
          AND views > 0
    """).fetchone()

    if not row or row[0] is None:
        return {}

    total_interactions = (row[6] or 0) + (row[7] or 0) + (row[8] or 0)

    return {
        "avg_engagement_rate": round(row[0], 1),
        "avg_likes": round(row[1], 1),
        "avg_replies": round(row[2], 1),
        "avg_reposts": round(row[3], 1),
        "avg_author_replies": round(row[5], 1) if row[5] else 0,
        "like_pct": round(row[6] / total_interactions * 100, 0) if total_interactions else 0,
        "reply_pct": round(row[7] / total_interactions * 100, 0) if total_interactions else 0,
        "repost_pct": round(row[8] / total_interactions * 100, 0) if total_interactions else 0,
        "post_count": row[9],
    }
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_db_helpers.py -v`
Expected: 全部 PASS

- [ ] **Step 5: 修改 insights_tracker.py 使用 db_helpers**

將 `insights_tracker.py` 中的 `get_trend` 和 `get_top_posts` 改為從 `db_helpers` import，原函式保留但加 deprecation 註解，避免破壞 main.py：

```python
# 在 insights_tracker.py 頂部加入
from threads_pipeline.db_helpers import get_trend, get_top_posts  # noqa: F811
```

注意：暫時不改 main.py 的 import，在 Task 6 統一處理。

- [ ] **Step 6: 跑全部測試**

Run: `python -m pytest -v`
Expected: 全部 PASS

- [ ] **Step 7: Commit**

```bash
git add db_helpers.py tests/test_db_helpers.py insights_tracker.py
git commit -m "refactor: 抽出 db_helpers 共用模組"
```

---

### Task 3: advisor analyze — 數據分析報告

**Files:**
- Create: `advisor.py`
- Create: `templates/advisor_report.md.j2`
- Create: `tests/test_advisor.py`

- [ ] **Step 1: 建立 tests/test_advisor.py 測試 analyze**

```python
"""advisor 測試。"""

import json
import sqlite3
import pytest
from pathlib import Path
from threads_pipeline.advisor import generate_analysis, generate_analysis_json


@pytest.fixture
def sample_db(tmp_path):
    """建立含範例數據的測試 DB。"""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE post_insights (
            collected_date TEXT NOT NULL, post_id TEXT NOT NULL,
            text_preview TEXT, full_text TEXT, posted_at TEXT,
            post_hour_local INTEGER, username TEXT,
            views INTEGER DEFAULT 0, likes INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0, reposts INTEGER DEFAULT 0,
            quotes INTEGER DEFAULT 0, author_reply_count INTEGER DEFAULT 0,
            PRIMARY KEY (collected_date, post_id)
        );
        CREATE TABLE account_insights (
            collected_date TEXT NOT NULL PRIMARY KEY,
            followers INTEGER DEFAULT 0, total_views INTEGER DEFAULT 0,
            total_likes INTEGER DEFAULT 0, total_replies INTEGER DEFAULT 0,
            total_reposts INTEGER DEFAULT 0
        );
        INSERT INTO post_insights VALUES
            ('2026-04-01', 'p1', '高表現AI文', '我是那種很依賴AI學習的人，尤其喜歡拿YouTube影片當素材', '2026-03-06T18:06:00+0000', 18, 'azuma01130626', 61485, 1200, 300, 200, 100, 12),
            ('2026-04-01', 'p2', '低表現教學文', '教學：如何設定環境變數，這是一個基礎的開發技巧', '2026-03-07T11:00:00+0000', 11, 'azuma01130626', 500, 10, 2, 1, 0, 0),
            ('2026-04-01', 'p3', '中等觀點文', '不知道大家有沒有試過，叫AI寫下它對你的觀察', '2026-03-08T19:28:00+0000', 19, 'azuma01130626', 353, 8, 4, 2, 1, 3);
        INSERT INTO account_insights VALUES
            ('2026-03-25', 200, 4000, 80, 40, 15),
            ('2026-04-01', 206, 5796, 110, 55, 22);
    """)
    conn.commit()
    conn.close()
    return db_path


class TestGenerateAnalysis:
    def test_normal_mode(self, sample_db, tmp_path):
        conn = sqlite3.connect(str(sample_db))
        report = generate_analysis(conn, "2026-04-02")
        conn.close()
        assert "帳號現況" in report
        assert "206" in report
        assert "Top" in report

    def test_empty_db(self, tmp_path):
        db_path = tmp_path / "empty.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript("""
            CREATE TABLE post_insights (
                collected_date TEXT NOT NULL, post_id TEXT NOT NULL,
                text_preview TEXT, full_text TEXT, posted_at TEXT,
                post_hour_local INTEGER, username TEXT,
                views INTEGER DEFAULT 0, likes INTEGER DEFAULT 0,
                replies INTEGER DEFAULT 0, reposts INTEGER DEFAULT 0,
                quotes INTEGER DEFAULT 0, author_reply_count INTEGER DEFAULT 0,
                PRIMARY KEY (collected_date, post_id)
            );
            CREATE TABLE account_insights (
                collected_date TEXT NOT NULL PRIMARY KEY,
                followers INTEGER DEFAULT 0, total_views INTEGER DEFAULT 0,
                total_likes INTEGER DEFAULT 0, total_replies INTEGER DEFAULT 0,
                total_reposts INTEGER DEFAULT 0
            );
        """)
        conn.commit()
        report = generate_analysis(conn, "2026-04-02")
        conn.close()
        assert "請先執行 Pipeline" in report


class TestGenerateAnalysisJson:
    def test_outputs_valid_json(self, sample_db):
        conn = sqlite3.connect(str(sample_db))
        result = generate_analysis_json(conn)
        conn.close()
        assert isinstance(result, dict)
        assert "followers" in result
        assert "avg_engagement_rate" in result
        assert "top_post_hours" in result
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_advisor.py -v`
Expected: FAIL

- [ ] **Step 3: 建立 templates/advisor_report.md.j2**

```
# 發文策略分析報告 — {{ report_date }}

> 產生於 {{ generated_at }} | 帳號: @{{ username }}

---
{% if mode == "no_data" %}
> ⚠️ 尚無數據，請先執行 Pipeline 收集數據。
{% elif mode == "degraded" %}
> ⚠️ 數據累積中（不足 7 天），以下為初步快照。

## 帳號現況

| 指標 | 數值 |
|------|------|
| 粉絲數 | {{ account.followers }} |
| 總觀看 | {{ account.total_views }} |

{% if top_posts %}
## 歷史表現 Top {{ top_posts | length }}

| # | 內容摘要 | 觀看 | 互動率 | 作者回覆 | 時段 |
|---|---------|------|--------|---------|------|
{% for p in top_posts %}| {{ loop.index }} | {{ p.text_preview }} | {{ p.views }} | {{ p.engagement_rate }}% | {{ p.author_reply_count }} | {{ p.post_hour_local }}:00 |
{% endfor %}{% endif %}
{% else %}
## 帳號現況

| 指標 | 數值 |
|------|------|
| 粉絲數 | {{ account.followers }}{% if trend %} ({{ trend.followers.delta | signdelta }}){% endif %} |
| 近 {{ trend.days }} 天觀看 | {{ account.total_views }} |
{% if trend %}| 粉絲變化 | {{ trend.followers.delta | signdelta }} ({{ trend.followers.pct }}%) |{% endif %}

## Creator Embedding 觀察

### 高表現貼文特徵
{% for p in top_posts[:3] %}
- **{{ p.text_preview }}**（觀看 {{ p.views }}，互動率 {{ p.engagement_rate }}%，作者回覆 {{ p.author_reply_count }} 則）
{% endfor %}

### 低表現貼文特徵
{% for p in bottom_posts[:3] %}
- **{{ p.text_preview }}**（觀看 {{ p.views }}，互動率 {{ p.engagement_rate }}%，作者回覆 {{ p.author_reply_count }} 則）
{% endfor %}

## Distribution Lifecycle 分析

- 上一篇發文：{{ last_post.posted_at_local }}（距今 {{ days_since_last }} 天）
- 上一篇表現：{{ last_post.views }} 觀看 / {{ last_post.engagement_rate }}% 互動率
- Freshness 狀態：{{ freshness_status }}
{% if days_since_last < 1 %}- ⚠️ 自打風險：距上篇不到 24 小時{% endif %}

### 歷史高表現發文時段
{% for hour, rate in hour_distribution.items() %}
- {{ hour }}:00 — 平均互動率 {{ rate }}%
{% endfor %}

## Engagement Economics 分析

- 平均互動率：{{ stats.avg_engagement_rate }}%
- 互動組成：按讚 {{ stats.like_pct }}% / 回覆 {{ stats.reply_pct }}% / 轉發 {{ stats.repost_pct }}%
- 作者平均回覆：{{ stats.avg_author_replies }} 則/篇
- 分析樣本：{{ stats.post_count }} 篇貼文

## 歷史表現 Top {{ top_posts | length }}

| # | 內容摘要 | 觀看 | 互動率 | 作者回覆 | 時段 |
|---|---------|------|--------|---------|------|
{% for p in top_posts %}| {{ loop.index }} | {{ p.text_preview }} | {{ p.views }} | {{ p.engagement_rate }}% | {{ p.author_reply_count }} | {{ p.post_hour_local }}:00 |
{% endfor %}{% endif %}

---
*由 Threads Pipeline V2.5 Advisor 自動產生*
```

- [ ] **Step 4: 建立 advisor.py 的 analyze 功能**

```python
"""發文顧問模組：數據分析 + Codex CLI 草稿審查。"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from threads_pipeline.db_helpers import (
    get_account_latest,
    get_engagement_stats,
    get_post_hour_distribution,
    get_top_posts,
    get_trend,
)

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


def _signdelta(value):
    if value > 0:
        return f"+{value}"
    return str(value)


def generate_analysis(conn, report_date: str, username: str = "azuma01130626") -> str:
    """產生分析報告 Markdown。根據數據量自動選擇模式。"""
    account = get_account_latest(conn)
    top_posts = get_top_posts(conn, limit=10)

    # 判斷模式
    if not account and not top_posts:
        mode = "no_data"
    elif not get_trend(conn):
        mode = "degraded"
    else:
        mode = "normal"

    # 計算互動率
    for p in top_posts:
        views = p.get("views", 0)
        if views > 0:
            engagement = p.get("likes", 0) + p.get("replies", 0) + p.get("reposts", 0) + p.get("quotes", 0)
            p["engagement_rate"] = round(engagement / views * 100, 1)
        else:
            p["engagement_rate"] = 0

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), keep_trailing_newline=True)
    env.filters["signdelta"] = _signdelta
    template = env.get_template("advisor_report.md.j2")

    # 準備模板數據
    context = {
        "report_date": report_date,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "username": username,
        "mode": mode,
        "account": account,
        "top_posts": top_posts[:5],
    }

    if mode == "normal":
        trend = get_trend(conn)
        stats = get_engagement_stats(conn)
        hour_dist = get_post_hour_distribution(conn)
        bottom_posts = sorted(top_posts, key=lambda p: p.get("views", 0))

        # 最近一篇貼文
        last_post = top_posts[0] if top_posts else {}
        if last_post.get("posted_at"):
            try:
                posted_dt = datetime.fromisoformat(last_post["posted_at"].replace("+0000", "+00:00"))
                days_since = (datetime.now(timezone.utc) - posted_dt).days
            except (ValueError, TypeError):
                days_since = 0
        else:
            days_since = 0

        # 按時間排序找最近的
        time_sorted = sorted(top_posts, key=lambda p: p.get("posted_at", ""), reverse=True)
        last_post = time_sorted[0] if time_sorted else {}
        if last_post.get("posted_at"):
            try:
                posted_dt = datetime.fromisoformat(last_post["posted_at"].replace("+0000", "+00:00"))
                days_since = (datetime.now(timezone.utc) - posted_dt).days
            except (ValueError, TypeError):
                days_since = 0

        if days_since > 3:
            freshness = "已過期，建議先暖場再發文"
        elif days_since > 1:
            freshness = "冷卻中，可以發文"
        else:
            freshness = "仍在 freshness 週期內"

        context.update({
            "trend": trend,
            "stats": stats,
            "hour_distribution": dict(list(hour_dist.items())[:5]),
            "bottom_posts": bottom_posts[:3],
            "last_post": last_post,
            "days_since_last": days_since,
            "freshness_status": freshness,
        })

    return template.render(**context)


def generate_analysis_json(conn) -> dict:
    """產生分析摘要 JSON（供 review 使用，控制 prompt 長度）。"""
    account = get_account_latest(conn)
    stats = get_engagement_stats(conn)
    hour_dist = get_post_hour_distribution(conn)
    top_posts = get_top_posts(conn, limit=5)
    trend = get_trend(conn)

    # Top 關鍵字（從 full_text 簡單提取）
    keywords = {}
    for p in top_posts:
        text = p.get("full_text", "") or ""
        for kw in ["AI", "Claude", "GPT", "Agent", "自動化", "工具", "經驗", "學習"]:
            if kw in text:
                keywords[kw] = keywords.get(kw, 0) + 1

    top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)

    # 最近一篇
    time_sorted = sorted(top_posts, key=lambda p: p.get("posted_at", ""), reverse=True)
    last_post = time_sorted[0] if time_sorted else {}
    days_since = 0
    if last_post.get("posted_at"):
        try:
            posted_dt = datetime.fromisoformat(last_post["posted_at"].replace("+0000", "+00:00"))
            days_since = (datetime.now(timezone.utc) - posted_dt).days
        except (ValueError, TypeError):
            pass

    return {
        "followers": account.get("followers", 0),
        "total_views": account.get("total_views", 0),
        "trend_days": trend["days"] if trend else 0,
        "follower_delta": trend["followers"]["delta"] if trend else 0,
        "avg_engagement_rate": stats.get("avg_engagement_rate", 0),
        "like_pct": stats.get("like_pct", 0),
        "reply_pct": stats.get("reply_pct", 0),
        "repost_pct": stats.get("repost_pct", 0),
        "avg_author_replies": stats.get("avg_author_replies", 0),
        "top_post_hours": list(hour_dist.keys())[:3],
        "top_content_keywords": [kw for kw, _ in top_keywords[:5]],
        "last_post_days_ago": days_since,
        "freshness": "expired" if days_since > 3 else "cooling" if days_since > 1 else "active",
        "post_count": stats.get("post_count", 0),
    }
```

- [ ] **Step 5: 跑測試確認通過**

Run: `python -m pytest tests/test_advisor.py -v`
Expected: 全部 PASS

- [ ] **Step 6: Commit**

```bash
git add advisor.py templates/advisor_report.md.j2 tests/test_advisor.py
git commit -m "feat: advisor analyze — 數據分析報告產出"
```

---

### Task 4: 文案結構框架 reference

**Files:**
- Create: `references/copywriting-frameworks.md`

- [ ] **Step 1: 建立 references/copywriting-frameworks.md**

完整的 16+1 結構框架文件（從 spec 的內容直接建立，包含每個結構的公式、適用場景、注意事項）。

```markdown
# 爆款文案腳本 16+1 結構

來源：魏育平（噯嚕嚕短影音行銷）課程簡報

---

## 結構總覽

| # | 名稱 | 公式 | 適用場景 |
|---|------|-----|---------|
| 01 | 引爆行動 | 觀點 → 危害 → 論據 → 結論 | 想改變讀者行為 |
| 02 | 破案解謎 | 疑問 → 描述 → 案例 → 總結 | 解答常見困惑 |
| 03 | 挑戰類 | 挑戰主題 → 有趣情節 → 輸出價值 | 分享挑戰過程 |
| 04 | SCQA | 情境 → 衝突 → 問題 → 答案 | 解決具體問題 |
| 05 | 三步循環 | 提問 → 設概念 → 解釋概念 | 解釋新概念 |
| 06 | 目標落地 | 美好目標 → 達成條件 | 激勵行動 |
| 07 | PREP | Point → Reason → Example → Point | 表達明確觀點 |
| 08 | 對比 | 錯誤操作 → 負面結果 → 正確方法 → 正向結果 | 教學糾正 |
| 09 | FIRE | Fact → Interpret → Reaction → Ends | 評論時事/趨勢 |
| 10 | 爆款人設 | 炸裂開頭 → 人設信息 → 高密度信息點 → 互動結尾 | 自我介紹/品牌建立 |
| 11 | 逆襲引流 | 積極結果 → 獲得感 → 方案 → 互動結尾 | 分享成功經驗 |
| 12 | 金句 | 金句 → 佐證 → 金句 → 佐證 | 觀點輸出 |
| 13 | 行業揭秘 | 行業揭秘 → 塑造期待 → 解決方案 | 分享內幕/專業知識 |
| 14 | 感性觀點 | 事實 → 感受 → 發現問題 → 結論 → 故事 → 總結 | 感性共鳴 |
| 15 | 通用類 | 鉤子開頭 → 塑造期待 → 解決方案 → 結尾 | 萬用結構 |
| 16 | 教知識經典 | 問題描述 → 問題拆解 → 答案描述 → 答案拆解 | 深度教學 |

## 4 類結尾

| 類型 | 特點 | 適用 |
|------|------|------|
| 互動式 | 引導留言、私訊、點讚 | 拉高互動數據 |
| 夥伴式 | 營造「我們是戰友」感 | 培養粉絲黏性 |
| Slogan | 品牌口號式收尾 | 品牌形象 |
| 反轉式 | 最後翻轉觀眾預期 | 記憶點 |

## 核心原則

1. 前 3 秒抓住眼球：讓觀眾願意停留下來
2. 節奏快、資訊集中：短時間內提供衝擊或啟發
3. 結尾誘導行動：呼籲留言、關注、私訊、下單等，實現轉化

## 選擇指南

- **分享個人經驗** → 03 挑戰類、11 逆襲引流、14 感性觀點
- **表達觀點** → 01 引爆行動、07 PREP、12 金句
- **教學知識** → 04 SCQA、05 三步循環、08 對比、16 教知識經典
- **評論趨勢** → 09 FIRE、02 破案解謎
- **品牌建立** → 10 爆款人設、13 行業揭秘
- **激勵行動** → 06 目標落地、15 通用類
```

- [ ] **Step 2: Commit**

```bash
git add references/copywriting-frameworks.md
git commit -m "docs: 新增 16+1 爆款文案結構框架"
```

---

### Task 5: advisor review — Codex CLI 草稿審查

**Files:**
- Modify: `advisor.py`
- Modify: `tests/test_advisor.py`

- [ ] **Step 1: 新增 review 測試**

在 `tests/test_advisor.py` 新增：

```python
from unittest.mock import patch, MagicMock
from threads_pipeline.advisor import review_draft, _build_review_prompt


class TestBuildReviewPrompt:
    def test_includes_draft(self):
        prompt = _build_review_prompt(
            draft="這是我的草稿",
            analysis_json={"followers": 206},
            plan_content=None,
        )
        assert "這是我的草稿" in prompt
        assert "206" in prompt

    def test_includes_plan_when_provided(self):
        prompt = _build_review_prompt(
            draft="草稿",
            analysis_json={},
            plan_content="## 目標受眾\n- 誰：AI 初學者",
        )
        assert "AI 初學者" in prompt

    def test_prompt_length_under_limit(self):
        prompt = _build_review_prompt(
            draft="短草稿",
            analysis_json={"followers": 206},
            plan_content="短 plan",
        )
        assert len(prompt) < 8000


class TestReviewDraft:
    @patch("threads_pipeline.advisor.subprocess.run")
    def test_successful_review(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="整體評分：⭐⭐⭐⭐ (4/5)\n\n✅ 鉤子 — 好",
        )
        result = review_draft("這是草稿", analysis_json={"followers": 206})
        assert "4/5" in result
        assert mock_run.called

    @patch("threads_pipeline.advisor.subprocess.run")
    def test_failed_review(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        result = review_draft("草稿", analysis_json={})
        assert "審查失敗" in result
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_advisor.py::TestBuildReviewPrompt -v`
Expected: FAIL

- [ ] **Step 3: 在 advisor.py 新增 review 功能**

```python
import subprocess

REVIEW_PROMPT_TEMPLATE = """你是一位 Threads 社群經營顧問，負責審查以下草稿。

## 審查標準（6 個維度）

1. 鉤子 — 前兩行能不能讓人停下來（前 3 秒抓住眼球）
2. 聚焦度 — 一篇一個切入點、一種人、一個問題
3. Takeaway — 讀完能帶走什麼，會不會想回覆
4. 定位一致性 — 跟歷史高表現內容方向是否一致
5. 受眾匹配 — 有沒有打中目標受眾的痛點{audience_note}
6. 結構完整性 — 是否符合文案結構要素，結尾是否有力{structure_note}

## 帳號數據摘要
{analysis_summary}

{plan_section}

## 待審查草稿
---
{draft}
---

請輸出：
1. 整體評分（1-5 星）
2. 每個維度用 ✅ / ⚠️ / ❌ 標記，加一句說明
3. 3-5 個具體的「建議行動」

用繁體中文回答。只輸出審查結果，不要重複草稿內容。"""


def _build_review_prompt(
    draft: str,
    analysis_json: dict,
    plan_content: str | None = None,
) -> str:
    """組合審查 prompt，控制在 8000 字以內。"""
    analysis_summary = json.dumps(analysis_json, ensure_ascii=False, indent=2) if analysis_json else "（無數據）"

    if plan_content:
        plan_section = f"## 發文規劃\n{plan_content[:2000]}"
        audience_note = "（參考發文規劃中的受眾設定）"
        structure_note = "（參考發文規劃中的建議結構）"
    else:
        plan_section = ""
        audience_note = "（無發文規劃，跳過此維度）"
        structure_note = "（無發文規劃，僅檢查基本結構）"

    prompt = REVIEW_PROMPT_TEMPLATE.format(
        analysis_summary=analysis_summary[:2000],
        plan_section=plan_section,
        draft=draft[:3000],
        audience_note=audience_note,
        structure_note=structure_note,
    )

    return prompt


def review_draft(
    draft: str,
    analysis_json: dict | None = None,
    plan_content: str | None = None,
    timeout: int = 60,
) -> str:
    """用 Codex CLI 審查草稿。回傳審查結果字串。"""
    prompt = _build_review_prompt(
        draft=draft,
        analysis_json=analysis_json or {},
        plan_content=plan_content,
    )

    try:
        result = subprocess.run(
            ["codex", "exec", "-s", "read-only", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
        )

        if result.returncode != 0:
            logger.warning("Codex 審查失敗 (exit %d): %s", result.returncode, result.stderr)
            return f"審查失敗（Codex exit code {result.returncode}）。請手動檢查草稿。\n\nstderr: {result.stderr[:500]}"

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        logger.warning("Codex 審查超時 (%ds)", timeout)
        return f"審查失敗（超時 {timeout} 秒）。請手動檢查草稿。"
    except FileNotFoundError:
        return "審查失敗：找不到 codex CLI。請確認已安裝。"
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_advisor.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add advisor.py tests/test_advisor.py
git commit -m "feat: advisor review — Codex CLI 草稿審查"
```

---

### Task 6: advisor CLI 入口

**Files:**
- Modify: `advisor.py`
- Modify: `.gitignore`

- [ ] **Step 1: 在 advisor.py 新增 CLI 入口**

在 `advisor.py` 底部新增：

```python
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Threads 發文顧問")
    subparsers = parser.add_subparsers(dest="command")

    # analyze
    analyze_parser = subparsers.add_parser("analyze", help="產生數據分析報告")
    analyze_parser.add_argument("--date", default=None, help="報告日期 (YYYY-MM-DD)")

    # review
    review_parser = subparsers.add_parser("review", help="審查草稿")
    review_parser.add_argument("file", nargs="?", help="草稿檔案路徑")
    review_parser.add_argument("--text", help="直接輸入草稿文字")
    review_parser.add_argument("--plan", help="指定 plan 檔案路徑")
    review_parser.add_argument("--analysis", help="指定 analysis JSON 路徑")

    args = parser.parse_args()

    if args.command == "analyze":
        _cmd_analyze(args)
    elif args.command == "review":
        _cmd_review(args)
    else:
        parser.print_help()


def _cmd_analyze(args):
    """執行 analyze 子指令。"""
    from threads_pipeline.main import _load_dotenv, load_config
    from threads_pipeline.db_helpers import get_readonly_connection

    _load_dotenv()
    config = load_config()

    report_date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    try:
        conn = get_readonly_connection(config)
    except FileNotFoundError as e:
        print(f"✗ {e}")
        print("  請先執行 Pipeline 收集數據")
        return

    # 產生報告
    report = generate_analysis(conn, report_date)

    # 產生 JSON 摘要
    analysis_json = generate_analysis_json(conn)
    conn.close()

    # 存檔
    output_dir = Path(__file__).parent / "output" / "advisor"
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / f"analysis_{report_date}.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"✓ 分析報告：{report_path}")

    json_path = output_dir / f"analysis_{report_date}.json"
    json_path.write_text(json.dumps(analysis_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ 審查摘要：{json_path}")


def _cmd_review(args):
    """執行 review 子指令。"""
    # 讀取草稿
    if args.file:
        draft_path = Path(args.file)
        if not draft_path.exists():
            print(f"✗ 找不到草稿檔案: {draft_path}")
            return
        draft = draft_path.read_text(encoding="utf-8")
        topic_id = draft_path.stem
    elif args.text:
        draft = args.text
        topic_id = "inline"
    else:
        print("✗ 請提供草稿檔案或 --text 參數")
        return

    if not draft.strip():
        print("✗ 草稿為空")
        return

    if len(draft) > 2000:
        print(f"⚠ 草稿偏長（{len(draft)} 字），建議精簡到 2000 字以內")

    # 讀取 analysis JSON
    analysis_json = {}
    if args.analysis:
        analysis_path = Path(args.analysis)
    else:
        # 自動找最新的
        advisor_dir = Path(__file__).parent / "output" / "advisor"
        json_files = sorted(advisor_dir.glob("analysis_*.json"), reverse=True)
        analysis_path = json_files[0] if json_files else None

    if analysis_path and analysis_path.exists():
        analysis_json = json.loads(analysis_path.read_text(encoding="utf-8"))
        print(f"✓ 讀取分析摘要：{analysis_path}")
    else:
        print("⚠ 找不到分析摘要，跳過數據維度")

    # 讀取 plan
    plan_content = None
    if args.plan:
        plan_path = Path(args.plan)
    else:
        # 自動找同名 plan
        plan_path = Path(f"drafts/{topic_id}.plan.md")

    if plan_path and plan_path.exists():
        plan_content = plan_path.read_text(encoding="utf-8")
        print(f"✓ 讀取發文規劃：{plan_path}")
    else:
        print("⚠ 找不到發文規劃，跳過受眾匹配和結構完整性維度")

    # 審查
    print("\n正在審查草稿（Codex CLI）...")
    result = review_draft(draft, analysis_json, plan_content)
    print("\n" + result)

    # 存檔
    if args.file:
        review_path = Path(f"drafts/{topic_id}.review.md")
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(result, encoding="utf-8")
        print(f"\n✓ 審查結果：{review_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 更新 .gitignore**

加入：
```
# Advisor
drafts/
output/advisor/
```

- [ ] **Step 3: 跑全部測試**

Run: `python -m pytest -v`
Expected: 全部 PASS

- [ ] **Step 4: Commit**

```bash
git add advisor.py .gitignore
git commit -m "feat: advisor CLI 入口 — analyze + review 子指令"
```

---

### Task 7: 整合測試 + 文件更新

**Files:**
- Modify: `docs/dev/roadmap.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: 手動測試 analyze**

```bash
cd C:\Users\user\OneDrive\桌面
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor analyze
```

Expected: 產出 `output/advisor/analysis_2026-04-02.md` 和 `.json`

- [ ] **Step 2: 手動測試 review**

```bash
echo "我最近在用 Claude Code 做一個 Threads 分析工具，分享一下過程中學到的事。" > drafts/test-post.txt
cd C:\Users\user\OneDrive\桌面
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor review threads_pipeline/drafts/test-post.txt
```

Expected: Codex 產出審查結果

- [ ] **Step 3: 更新 CLAUDE.md 加入 advisor 指令**

在 Commands 區塊加入：
```bash
# Run advisor analyze
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor analyze

# Run advisor review
$env:PYTHONUTF8=1; python -m threads_pipeline.advisor review drafts/my-post.txt
```

- [ ] **Step 4: 更新 roadmap.md**

將 V2.5 狀態從「構想」改為「開發中」或「已完成」。

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md docs/dev/roadmap.md
git commit -m "docs: V2.5 貼文健檢功能上線 — 更新文件"
```

---

## Self-Review Checklist

1. **Spec coverage:** ✅ Schema 擴充、analyze、review、copywriting frameworks、CLI 入口、降級模式、邊界處理
2. **Placeholder scan:** ✅ 所有步驟都有完整程式碼
3. **Type consistency:** ✅ `generate_analysis`, `generate_analysis_json`, `review_draft`, `_build_review_prompt` 簽名一致
