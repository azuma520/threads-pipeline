"""Threads API 封裝：關鍵字搜尋、去重、時間過濾。"""

import logging
import time
from datetime import datetime, timedelta, timezone

import requests

logger = logging.getLogger(__name__)

THREADS_API_BASE = "https://graph.threads.net/v1.0"


def fetch_posts(config: dict) -> list[dict]:
    """對所有關鍵字搜尋，去重後回傳貼文列表。"""
    threads_cfg = config["threads"]
    token = threads_cfg["access_token"]
    keywords = threads_cfg["keywords"]
    sort_order = threads_cfg.get("sort", "TOP")
    max_per_kw = threads_cfg.get("max_posts_per_keyword", 25)

    # 時間範圍：昨天 00:00 ~ 今天 00:00 UTC
    now = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    since = now - timedelta(days=1)
    until = now

    seen_ids: set[str] = set()
    all_posts: list[dict] = []

    for kw in keywords:
        print(f"  搜尋關鍵字: {kw}...", end=" ")
        try:
            raw_posts = _search_keyword(
                keyword=kw,
                token=token,
                sort_order=sort_order,
                max_results=max_per_kw,
                since=since,
                until=until,
            )
        except Exception as e:
            logger.warning("關鍵字 '%s' 搜尋失敗: %s", kw, e)
            print(f"失敗（{e}）")
            continue

        new_count = 0
        for post in raw_posts:
            pid = post["id"]
            if pid not in seen_ids:
                seen_ids.add(pid)
                post["keyword_matched"] = kw
                all_posts.append(post)
                new_count += 1

        print(f"取得 {len(raw_posts)} 篇，新增 {new_count} 篇")

    return all_posts


def _search_keyword(
    keyword: str,
    token: str,
    sort_order: str = "TOP",
    max_results: int = 25,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[dict]:
    """單一關鍵字搜尋，含重試邏輯。"""
    params = {
        "q": keyword,
        "sort": sort_order,
        "access_token": token,
        "fields": "id,text,username,timestamp,like_count,permalink",
        "limit": min(max_results, 25),
    }
    if since:
        params["since"] = int(since.timestamp())
    if until:
        params["until"] = int(until.timestamp())

    url = f"{THREADS_API_BASE}/keyword_search"
    data = _request_with_retry(url, params)

    posts = data.get("data", [])
    return posts[:max_results]


def _request_with_retry(
    url: str, params: dict, max_retries: int = 3
) -> dict:
    """GET 請求，指數退避重試。"""
    session = requests.Session()

    for attempt in range(max_retries):
        try:
            resp = session.get(url, params=params, timeout=30)

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 2 ** attempt))
                logger.warning("Rate limited, 等待 %ds...", retry_after)
                time.sleep(retry_after)
                continue

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            logger.warning("請求失敗 (attempt %d/%d): %s, 等待 %ds",
                           attempt + 1, max_retries, e, wait)
            time.sleep(wait)

    return {"data": []}
