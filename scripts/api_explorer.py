"""Threads API 功能邊界探索腳本 — 系統性測試 keyword_search 參數組合。"""

import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 載入 .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

import requests

TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "")
BASE = "https://graph.threads.net/v1.0"
RESULTS = []


def api_get(url, params, label=""):
    """發送 GET 請求，回傳 (status_code, json_or_text, headers, elapsed_ms)。"""
    params["access_token"] = TOKEN
    try:
        resp = requests.get(url, params=params, timeout=30)
        elapsed = int(resp.elapsed.total_seconds() * 1000)
        try:
            body = resp.json()
        except Exception:
            body = resp.text[:500]
        return resp.status_code, body, dict(resp.headers), elapsed
    except Exception as e:
        return 0, str(e), {}, 0


def record(test_id, description, params_used, status, body, headers, elapsed, notes=""):
    """記錄測試結果。"""
    data_count = len(body.get("data", [])) if isinstance(body, dict) else 0
    result = {
        "test_id": test_id,
        "description": description,
        "params": params_used,
        "status": status,
        "data_count": data_count,
        "elapsed_ms": elapsed,
        "notes": notes,
    }
    # 擷取前 3 筆 data 作為樣本
    if isinstance(body, dict) and body.get("data"):
        result["sample"] = body["data"][:3]
    if isinstance(body, dict) and body.get("paging"):
        result["paging"] = body["paging"]
    if isinstance(body, dict) and body.get("error"):
        result["error"] = body["error"]

    RESULTS.append(result)
    status_icon = "✓" if status == 200 else "✗"
    print(f"  {status_icon} [{test_id}] {description} — {status}, {data_count} 筆, {elapsed}ms")
    if notes:
        print(f"    → {notes}")
    return result


def test_1_search_type():
    """測試 search_type: TOP vs RECENT。"""
    print("\n=== 1. search_type 比較 ===")
    url = f"{BASE}/keyword_search"
    fields = "id,text,username,timestamp"

    # 1a: TOP
    params = {"q": "AI", "search_type": "TOP", "fields": fields, "limit": 10}
    s, b, h, e = api_get(url, params)
    r_top = record("1a", "search_type=TOP", params, s, b, h, e)

    time.sleep(1)

    # 1b: RECENT
    params = {"q": "AI", "search_type": "RECENT", "fields": fields, "limit": 10}
    s, b, h, e = api_get(url, params)
    r_recent = record("1b", "search_type=RECENT", params, s, b, h, e)

    # 1c: 比較重疊度
    if r_top.get("sample") and r_recent.get("sample"):
        top_ids = {p["id"] for p in r_top.get("sample", [])}
        recent_ids = {p["id"] for p in r_recent.get("sample", [])}
        overlap = top_ids & recent_ids
        record("1c", "TOP vs RECENT 重疊度", {}, 200, {}, {}, 0,
               f"TOP 取 {len(top_ids)} 篇, RECENT 取 {len(recent_ids)} 篇, 重疊 {len(overlap)} 篇")

    time.sleep(1)


def test_2_search_mode():
    """測試 search_mode: KEYWORD vs TAG。"""
    print("\n=== 2. search_mode 比較 ===")
    url = f"{BASE}/keyword_search"
    fields = "id,text,username,timestamp"

    # 2a: KEYWORD (預設)
    params = {"q": "AI", "search_mode": "KEYWORD", "fields": fields, "limit": 10}
    s, b, h, e = api_get(url, params)
    record("2a", "search_mode=KEYWORD", params, s, b, h, e)

    time.sleep(1)

    # 2b: TAG
    params = {"q": "AI", "search_mode": "TAG", "fields": fields, "limit": 10}
    s, b, h, e = api_get(url, params)
    record("2b", "search_mode=TAG (英文)", params, s, b, h, e)

    time.sleep(1)

    # 2c: TAG 搜中文
    params = {"q": "人工智慧", "search_mode": "TAG", "fields": fields, "limit": 10}
    s, b, h, e = api_get(url, params)
    record("2c", "search_mode=TAG (中文)", params, s, b, h, e)

    time.sleep(1)


def test_3_author_username():
    """測試 author_username 篩選。"""
    print("\n=== 3. author_username 篩選 ===")
    url = f"{BASE}/keyword_search"
    fields = "id,text,username,timestamp"

    # 3a: 搜自己
    params = {"q": "AI", "author_username": "azuma01130626", "fields": fields, "limit": 10}
    s, b, h, e = api_get(url, params)
    record("3a", "author=自己 (azuma01130626)", params, s, b, h, e)

    time.sleep(1)

    # 3b: 搜知名帳號
    params = {"q": "AI", "author_username": "zaborsky", "fields": fields, "limit": 10}
    s, b, h, e = api_get(url, params)
    record("3b", "author=知名帳號 (zaborsky)", params, s, b, h, e)

    time.sleep(1)

    # 3c: 不存在的 username
    params = {"q": "AI", "author_username": "zzz_nonexistent_user_999", "fields": fields, "limit": 10}
    s, b, h, e = api_get(url, params)
    record("3c", "author=不存在帳號", params, s, b, h, e)

    time.sleep(1)

    # 3d: author + 無關關鍵字
    params = {"q": "量子力學微積分", "author_username": "azuma01130626", "fields": fields, "limit": 10}
    s, b, h, e = api_get(url, params)
    record("3d", "author=自己 + 無關關鍵字", params, s, b, h, e)

    time.sleep(1)


def test_4_media_type():
    """測試 media_type 篩選。"""
    print("\n=== 4. media_type 篩選 ===")
    url = f"{BASE}/keyword_search"
    fields = "id,text,username,timestamp,media_type"

    for test_id, mt, desc in [
        ("4a", "TEXT_POST", "media_type=TEXT_POST"),
        ("4b", "IMAGE", "media_type=IMAGE"),
        ("4c", "VIDEO", "media_type=VIDEO"),
    ]:
        params = {"q": "AI", "media_type": mt, "fields": fields, "limit": 10}
        s, b, h, e = api_get(url, params)
        record(test_id, desc, params, s, b, h, e)
        time.sleep(1)

    # 4d: 不帶 media_type
    params = {"q": "AI", "fields": fields, "limit": 10}
    s, b, h, e = api_get(url, params)
    record("4d", "不帶 media_type", params, s, b, h, e)

    time.sleep(1)


def test_5_limit_paging():
    """測試 limit 和分頁。"""
    print("\n=== 5. limit 和分頁 ===")
    url = f"{BASE}/keyword_search"
    fields = "id,text,username,timestamp"

    # 5a: limit=1
    params = {"q": "AI", "fields": fields, "limit": 1}
    s, b, h, e = api_get(url, params)
    record("5a", "limit=1", params, s, b, h, e)
    time.sleep(1)

    # 5b: limit=100
    params = {"q": "AI", "fields": fields, "limit": 100}
    s, b, h, e = api_get(url, params)
    record("5b", "limit=100", params, s, b, h, e)
    time.sleep(1)

    # 5c: limit=101
    params = {"q": "AI", "fields": fields, "limit": 101}
    s, b, h, e = api_get(url, params)
    record("5c", "limit=101 (超過最大值)", params, s, b, h, e)
    time.sleep(1)

    # 5d: 分頁測試
    print("  分頁測試...")
    params = {"q": "AI", "fields": fields, "limit": 25}
    total_fetched = 0
    page = 0
    while page < 5:  # 最多翻 5 頁
        s, b, h, e = api_get(url, params)
        if s != 200 or not isinstance(b, dict):
            break
        count = len(b.get("data", []))
        total_fetched += count
        page += 1
        paging = b.get("paging", {})
        cursors = paging.get("cursors", {})
        next_cursor = cursors.get("after")
        print(f"    第 {page} 頁: {count} 筆")
        if not next_cursor or count == 0:
            break
        params = {"q": "AI", "fields": fields, "limit": 25, "after": next_cursor}
        time.sleep(1)

    record("5d", f"分頁測試: 翻了 {page} 頁", {}, 200, {}, {}, 0,
           f"共取得 {total_fetched} 篇")
    time.sleep(1)


def test_6_time_range():
    """測試 since / until 時間範圍。"""
    print("\n=== 6. since / until 時間範圍 ===")
    url = f"{BASE}/keyword_search"
    fields = "id,text,username,timestamp"
    now = datetime.now(timezone.utc)

    # 6a: 過去 24 小時
    since_ts = int((now - timedelta(hours=24)).timestamp())
    until_ts = int(now.timestamp())
    params = {"q": "AI", "fields": fields, "limit": 25, "since": since_ts, "until": until_ts}
    s, b, h, e = api_get(url, params)
    record("6a", "過去 24 小時", params, s, b, h, e)
    time.sleep(1)

    # 6b: 過去 7 天
    since_ts = int((now - timedelta(days=7)).timestamp())
    params = {"q": "AI", "fields": fields, "limit": 25, "since": since_ts, "until": until_ts}
    s, b, h, e = api_get(url, params)
    record("6b", "過去 7 天", params, s, b, h, e)
    time.sleep(1)

    # 6c: 過去 30 天
    since_ts = int((now - timedelta(days=30)).timestamp())
    params = {"q": "AI", "fields": fields, "limit": 25, "since": since_ts, "until": until_ts}
    s, b, h, e = api_get(url, params)
    record("6c", "過去 30 天", params, s, b, h, e)
    time.sleep(1)

    # 6d: 不帶 since/until
    params = {"q": "AI", "fields": fields, "limit": 25}
    s, b, h, e = api_get(url, params)
    record("6d", "不帶 since/until", params, s, b, h, e)
    time.sleep(1)


def test_7_fields():
    """測試 fields 可回傳欄位。"""
    print("\n=== 7. fields 可回傳欄位 ===")
    url = f"{BASE}/keyword_search"

    field_tests = [
        ("7a", "id,text,username,timestamp", "基本欄位"),
        ("7b", "id,text,username,timestamp,has_replies,is_quote_post,is_reply", "互動相關"),
        ("7c", "id,text,username,timestamp,media_type,media_url,thumbnail_url", "媒體相關"),
        ("7d", "id,text,username,timestamp,topic_tag", "topic_tag"),
        ("7e", "id,text,username,timestamp,link_attachment_url", "連結附件"),
        ("7f", "id,text,username,timestamp,poll_attachment", "投票"),
        ("7g", "id,text,username,timestamp,like_count", "like_count"),
    ]

    for test_id, fields, desc in field_tests:
        params = {"q": "AI", "fields": fields, "limit": 3}
        s, b, h, e = api_get(url, params)
        # 記錄實際回傳的欄位
        actual_fields = []
        if isinstance(b, dict) and b.get("data"):
            actual_fields = list(b["data"][0].keys())
        notes = f"回傳欄位: {actual_fields}" if actual_fields else ""
        record(test_id, f"fields: {desc}", {"fields": fields}, s, b, h, e, notes)
        time.sleep(1)

    # 7h: 全部欄位
    all_fields = "id,text,username,timestamp,like_count,has_replies,is_quote_post,is_reply,media_type,media_url,thumbnail_url,topic_tag,link_attachment_url,poll_attachment,permalink"
    params = {"q": "AI", "fields": all_fields, "limit": 3}
    s, b, h, e = api_get(url, params)
    actual_fields = []
    if isinstance(b, dict) and b.get("data"):
        actual_fields = list(b["data"][0].keys())
    record("7h", "全部欄位", {"fields": all_fields}, s, b, h, e,
           f"回傳欄位: {actual_fields}")
    time.sleep(1)


def test_8_rate_limit():
    """觀察 Rate Limit。"""
    print("\n=== 8. Rate Limit 觀察 ===")
    url = f"{BASE}/keyword_search"
    fields = "id,text,username,timestamp"

    print("  連續送 10 個快速請求...")
    statuses = []
    all_headers = {}
    for i in range(10):
        params = {"q": f"AI test{i}", "fields": fields, "limit": 1}
        s, b, h, e = api_get(url, params)
        statuses.append(s)
        if i == 0:
            # 記錄第一次的完整 headers
            all_headers = h
        if s == 429:
            print(f"    第 {i+1} 次被限速！")
            break

    # 找 rate limit 相關的 header
    rl_headers = {k: v for k, v in all_headers.items()
                  if any(x in k.lower() for x in ["rate", "limit", "retry", "x-"])}

    record("8a", f"連續 {len(statuses)} 次快速請求", {},
           200 if all(s == 200 for s in statuses) else 429,
           {}, {}, 0,
           f"狀態碼: {statuses}")
    record("8b", "Rate limit 相關 headers", {},
           200, {}, {}, 0,
           f"Headers: {rl_headers if rl_headers else '無 rate limit headers'}")


def test_9_search_quality():
    """測試搜尋品質。"""
    print("\n=== 9. 搜尋品質 ===")
    url = f"{BASE}/keyword_search"
    fields = "id,text,username,timestamp"

    # 9a: 中文關鍵字
    params = {"q": "人工智慧", "fields": fields, "limit": 10}
    s, b, h, e = api_get(url, params)
    record("9a", "中文關鍵字「人工智慧」", params, s, b, h, e)
    time.sleep(1)

    # 9b: 多字詞
    params = {"q": "AI Agent 自動化", "fields": fields, "limit": 10}
    s, b, h, e = api_get(url, params)
    record("9b", "多字詞「AI Agent 自動化」", params, s, b, h, e)
    time.sleep(1)

    # 9c: 特殊字元
    params = {"q": "C++ #coding", "fields": fields, "limit": 10}
    s, b, h, e = api_get(url, params)
    record("9c", "特殊字元「C++ #coding」", params, s, b, h, e)


def main():
    if not TOKEN:
        print("✗ 缺少 THREADS_ACCESS_TOKEN，請檢查 .env")
        sys.exit(1)

    print(f"=== Threads API 功能邊界探索 ===")
    print(f"時間: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    # 先驗證 token
    print("\n驗證 Token...")
    s, b, h, e = api_get(f"{BASE}/me", {})
    if s != 200:
        print(f"✗ Token 無效 ({s}): {b}")
        sys.exit(1)
    print(f"✓ Token 有效 (user: {b.get('id', '?')})")

    # 執行所有測試
    test_1_search_type()
    test_2_search_mode()
    test_3_author_username()
    test_4_media_type()
    test_5_limit_paging()
    test_6_time_range()
    test_7_fields()
    test_8_rate_limit()
    test_9_search_quality()

    # 輸出結果 JSON
    output_path = Path(__file__).parent.parent / "docs" / "dev" / "api-exploration-raw.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(RESULTS, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n=== 完成！共 {len(RESULTS)} 項測試 ===")
    print(f"原始結果: {output_path}")

    # 輸出摘要
    passed = sum(1 for r in RESULTS if r["status"] == 200)
    failed = sum(1 for r in RESULTS if r["status"] != 200 and r["status"] != 0)
    print(f"成功: {passed}, 失敗: {failed}, 其他: {len(RESULTS) - passed - failed}")


if __name__ == "__main__":
    main()
