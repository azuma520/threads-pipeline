"""Threads API 封裝：關鍵字搜尋、去重、時間過濾、Token 管理。"""

import logging
import re
import time
from datetime import datetime, timedelta, timezone

import requests

logger = logging.getLogger(__name__)

THREADS_API_BASE = "https://graph.threads.net/v1.0"
THREADS_API_ROOT = "https://graph.threads.net"


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
    """GET with exponential backoff.

    4xx client errors raise immediately (no retry, no URL logged — avoids
    leaking access_token into logs / recordings). 5xx and network errors
    retry with backoff; log messages strip the `" for url: ..."` suffix
    that `requests` appends (which would otherwise expose the token).
    """
    session = requests.Session()

    for attempt in range(max_retries):
        try:
            resp = session.get(url, params=params, timeout=30)

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 2 ** attempt))
                logger.warning("Rate limited, waiting %ds...", retry_after)
                time.sleep(retry_after)
                continue

            if 400 <= resp.status_code < 500:
                resp.raise_for_status()

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else 0
            if status and 400 <= status < 500:
                raise
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            logger.warning(
                "Server error (attempt %d/%d): HTTP %d, waiting %ds",
                attempt + 1, max_retries, status, wait,
            )
            time.sleep(wait)

        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            msg = str(e).split(" for url:")[0]
            logger.warning(
                "Request failed (attempt %d/%d): %s, waiting %ds",
                attempt + 1, max_retries, msg, wait,
            )
            time.sleep(wait)

    return {"data": []}


def validate_token(token: str) -> dict:
    """驗證 Token 是否有效，成功回傳使用者資料 dict（含 id）。

    失敗時 raise Exception，錯誤訊息說明原因。
    """
    url = f"{THREADS_API_BASE}/me"
    params = {"access_token": token}
    try:
        data = _request_with_retry(url, params)
    except requests.exceptions.HTTPError as e:
        raise Exception("Token 無效或已過期，請重新取得") from e
    except requests.exceptions.RequestException as e:
        raise Exception(f"Token 驗證時發生網路錯誤：{e}") from e

    if "id" not in data:
        raise Exception("Token 驗證回應格式異常，缺少使用者 id")

    return data


def refresh_token(token: str) -> str | None:
    """嘗試續期 Long-lived Token，成功回傳新 token 字串，失敗回傳 None。

    注意：只有尚未過期的 long-lived token 才能續期。
    """
    url = f"{THREADS_API_ROOT}/refresh_access_token"
    params = {
        "grant_type": "th_refresh_token",
        "access_token": token,
    }
    try:
        data = _request_with_retry(url, params)
        new_token = data.get("access_token")
        if not new_token:
            logger.warning("Token 續期回應中未找到 access_token 欄位")
            return None
        return new_token
    except Exception as e:
        logger.warning("Token 續期失敗（可能已完全過期）：%s", e)
        return None


# ═══════════════════════════════════════════════════════════════════════════
# 批次 B2：CLI 唯讀指令專用的公開 helper
#
# 設計原則：
#   - 全部透過 _request_with_retry 走 GET（保留既有 429 退避邏輯）
#   - 回傳 dict 結構盡量貼近 API 原始格式，CLI 層負責轉成人讀 / envelope
#   - 分頁 helpers（list_my_posts / fetch_post_replies）統一回 {"<items>": [...], "next_cursor": str | None}
# ═══════════════════════════════════════════════════════════════════════════

_DEFAULT_POST_FIELDS = "id,text,timestamp,media_type,permalink,username"
_DEFAULT_REPLY_FIELDS = "id,text,timestamp,username"
_DEFAULT_ACCOUNT_FIELDS = "id,username,threads_profile_picture_url,threads_biography"
_DEFAULT_MENTION_FIELDS = "id,text,username,timestamp,permalink"


def fetch_account_info(token: str) -> dict:
    """GET /me — 帳號基本資料。"""
    url = f"{THREADS_API_BASE}/me"
    params = {
        "access_token": token,
        "fields": _DEFAULT_ACCOUNT_FIELDS,
    }
    return _request_with_retry(url, params)


def fetch_account_insights_cli(token: str) -> dict:
    """GET /me/threads_insights — 帳號 insights（followers / views 等）。

    注意：與 insights_tracker._fetch_account_insights 刻意分開——pipeline 的
    版本針對 SQLite upsert 定制化欄位、CLI 版本回傳 API 原樣給 envelope 使用。
    """
    url = f"{THREADS_API_BASE}/me/threads_insights"
    params = {
        "access_token": token,
        "metric": "views,likes,replies,reposts,quotes,followers_count",
    }
    return _request_with_retry(url, params)


def list_my_posts(
    token: str,
    limit: int = 25,
    cursor: str | None = None,
) -> dict:
    """GET /me/threads — 自己的貼文列表，支援分頁。

    回傳：
        {"posts": [...], "next_cursor": "..." | None}
    """
    url = f"{THREADS_API_BASE}/me/threads"
    params: dict = {
        "access_token": token,
        "limit": limit,
        "fields": _DEFAULT_POST_FIELDS,
    }
    if cursor:
        params["after"] = cursor
    data = _request_with_retry(url, params)
    next_cursor = data.get("paging", {}).get("cursors", {}).get("after")
    return {"posts": data.get("data", []), "next_cursor": next_cursor}


def list_mentions(
    token: str,
    limit: int = 25,
    cursor: str | None = None,
) -> dict:
    """GET /me/threads_mentions — 查詢 @ 自己帳號的 mentions，支援分頁。

    回傳：
        {"mentions": [...], "next_cursor": "..." | None}
    """
    url = f"{THREADS_API_BASE}/me/threads_mentions"
    params: dict = {
        "access_token": token,
        "limit": limit,
        "fields": _DEFAULT_MENTION_FIELDS,
    }
    if cursor:
        params["after"] = cursor
    data = _request_with_retry(url, params)
    next_cursor = data.get("paging", {}).get("cursors", {}).get("after")
    return {"mentions": data.get("data", []), "next_cursor": next_cursor}


def fetch_post_detail(
    post_id: str,
    token: str,
    fields: str | None = None,
) -> dict:
    """GET /{post_id} — 單則貼文詳情。

    fields 可自訂——delete 備份會傳更完整的欄位集（含 permalink / timestamp）。
    """
    url = f"{THREADS_API_BASE}/{post_id}"
    params = {
        "access_token": token,
        "fields": fields or _DEFAULT_POST_FIELDS,
    }
    return _request_with_retry(url, params)


def fetch_post_insights_cli(post_id: str, token: str) -> dict:
    """GET /{post_id}/insights — 單則貼文 insights。"""
    url = f"{THREADS_API_BASE}/{post_id}/insights"
    params = {
        "access_token": token,
        "metric": "views,likes,replies,reposts,quotes",
    }
    return _request_with_retry(url, params)


def fetch_post_replies(
    post_id: str,
    token: str,
    limit: int = 25,
    cursor: str | None = None,
) -> dict:
    """GET /{post_id}/replies — 貼文回覆列表，支援分頁。

    回傳：
        {"replies": [...], "next_cursor": "..." | None}
    """
    url = f"{THREADS_API_BASE}/{post_id}/replies"
    params: dict = {
        "access_token": token,
        "limit": limit,
        "fields": _DEFAULT_REPLY_FIELDS,
    }
    if cursor:
        params["after"] = cursor
    data = _request_with_retry(url, params)
    next_cursor = data.get("paging", {}).get("cursors", {}).get("after")
    return {"replies": data.get("data", []), "next_cursor": next_cursor}


def delete_post(post_id: str, token: str) -> bool:
    """DELETE /{post_id} — 刪除貼文。

    Returns:
        True on success.

    Raises:
        requests.exceptions.HTTPError: 4xx / 5xx response。
        requests.exceptions.RequestException: 網路 / timeout。

    注意：此函式**不**走 `_request_with_retry`（DELETE 非 idempotent 的 retry
    在 Threads API 定義不明；寧可失敗交由使用者決定，不自動重試）。
    """
    url = f"{THREADS_API_BASE}/{post_id}"
    params = {"access_token": token}
    resp = requests.delete(url, params=params, timeout=30)
    resp.raise_for_status()
    return True


# ═══════════════════════════════════════════════════════════════════════════
# profile_discovery helpers（App Review 2026-04-23 本輪送審範圍）
#
# 注意：`/{username}` 與 `/{username}/threads` 在 `threads_profile_discovery`
# 核准前**完全鎖住**（即使對 app owner 自己的 username 亦同），實測回 HTTP 400
# `Object with ID '<username>' does not exist, cannot be loaded due to missing
# permissions`。核准後才可用於跨帳號讀取。
#
# 本批 helper 為前瞻實作：單元測試用 mock，無 live smoke 可跑；demo 影片走
# Architecture-Demo 並誠實展示這個 400 錯誤（見 docs/app-review/
# demo-script-profile-discovery.md Plan B Step 6）。
# ═══════════════════════════════════════════════════════════════════════════

_DEFAULT_PROFILE_FIELDS = "id,username,threads_biography,threads_profile_picture_url"
_DEFAULT_USER_THREADS_FIELDS = "id,text,permalink,timestamp,username"


def fetch_user_profile(username: str, token: str) -> dict:
    """GET /{username} — 讀他人（或自己）的 Threads profile 基本資料。

    Args:
        username: Threads username（不含 @ 符號）。
        token: Access token。

    Returns:
        API dict，含 id / username / threads_biography 等欄位。

    Raises:
        requests.exceptions.HTTPError: 4xx / 5xx。**核准前對任何 username 都會回
            HTTP 400**（endpoint 本身 permission-gated）。
        requests.exceptions.RequestException: 網路 / timeout。
    """
    url = f"{THREADS_API_BASE}/{username}"
    params = {
        "access_token": token,
        "fields": _DEFAULT_PROFILE_FIELDS,
    }
    return _request_with_retry(url, params)


def fetch_user_threads(
    username: str,
    token: str,
    limit: int = 25,
    cursor: str | None = None,
) -> dict:
    """GET /{username}/threads — 列他人（或自己）的公開貼文，支援分頁。

    Args:
        username: Threads username（不含 @）。
        token: Access token。
        limit: 單次回傳數量（Threads API 上限 100，呼叫端已 clamp）。
        cursor: 分頁 cursor；若有則傳 `after`。

    Returns:
        {"posts": [...], "next_cursor": str | None}。格式對齊 list_my_posts。

    Raises:
        requests.exceptions.HTTPError: 同 fetch_user_profile，核准前會 400。
        requests.exceptions.RequestException: 網路 / timeout。
    """
    url = f"{THREADS_API_BASE}/{username}/threads"
    params: dict = {
        "access_token": token,
        "limit": limit,
        "fields": _DEFAULT_USER_THREADS_FIELDS,
    }
    if cursor:
        params["after"] = cursor
    data = _request_with_retry(url, params)
    next_cursor = data.get("paging", {}).get("cursors", {}).get("after")
    return {"posts": data.get("data", []), "next_cursor": next_cursor}


# URL → (username, shortcode) 解析
# 主要支援：https://www.threads.com/@{username}/post/{shortcode}
# 也支援：threads.net（舊域名）、無 www、有 trailing slash / query string
_THREADS_URL_RE = re.compile(
    r"^https?://(?:www\.)?threads\.(?:com|net)/@([^/?#]+)/post/([A-Za-z0-9_-]+)(?:[/?#].*)?$",
    re.IGNORECASE,
)


def parse_threads_post_url(url: str) -> tuple[str, str]:
    """解析 Threads post URL → (username, shortcode)。

    Raises:
        ValueError: URL 格式不符。短格式 `threads.com/t/{shortcode}` 不含
            username，無法透過 profile_discovery 解析，此函式會 raise。
    """
    m = _THREADS_URL_RE.match(url.strip())
    if not m:
        raise ValueError(
            "URL must be in form `https://www.threads.com/@username/post/shortcode`"
        )
    return m.group(1), m.group(2)


def resolve_post_by_url(url: str, token: str, search_limit: int = 25) -> dict:
    """URL-first helper：用 URL 找到對應 post dict（含 text）。

    流程：
        1. parse URL → (username, shortcode)
        2. GET /{username}/threads?limit=search_limit
        3. 在回傳列表中匹配 permalink 包含 shortcode 的 post
        4. 回傳該 post dict

    Args:
        url: Threads post 公開 URL。
        token: Access token。
        search_limit: 列表查詢量；shortcode 不在最近 N 則會回 LookupError。

    Returns:
        匹配到的 post dict（含 id / text / permalink / timestamp / username）。

    Raises:
        ValueError: URL 格式不符（見 parse_threads_post_url）。
        LookupError: URL 解析成功但 shortcode 不在該 user 最近 search_limit
            則貼文中。
        requests.exceptions.HTTPError: Graph API 4xx/5xx，含核准前必然的 400。
        requests.exceptions.RequestException: 網路 / timeout。
    """
    username, shortcode = parse_threads_post_url(url)
    result = fetch_user_threads(username, token, limit=search_limit)
    for post in result["posts"]:
        permalink = post.get("permalink") or ""
        if shortcode in permalink:
            return post
    raise LookupError(
        f"Post shortcode `{shortcode}` not found in `{username}`'s recent "
        f"{search_limit} posts"
    )


def hide_reply(reply_id: str, token: str, hide: bool = True) -> bool:
    """POST /{reply_id}/manage_reply — 隱藏或取消隱藏回覆。

    Args:
        reply_id: 要操作的 reply ID（是別人對你貼文的回覆 ID）。
        token: Access token。
        hide: True=隱藏、False=取消隱藏。

    Returns:
        True on success.

    Raises:
        requests.exceptions.HTTPError: 4xx/5xx。
        requests.exceptions.RequestException: 網路 / timeout。

    注意：與 delete_post 一樣不走 _request_with_retry——POST 有副作用，
    重試語意不明；失敗交由呼叫端決定。
    """
    url = f"{THREADS_API_BASE}/{reply_id}/manage_reply"
    params = {
        "access_token": token,
        "hide": "true" if hide else "false",
    }
    resp = requests.post(url, params=params, timeout=30)
    resp.raise_for_status()
    return True
