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
