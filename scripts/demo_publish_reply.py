"""展示 threads_content_publish 和 threads_manage_replies 的 Demo 腳本。"""

import os
import sys
import time
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


def main():
    print("=== Demo: threads_content_publish + threads_manage_replies ===\n")

    # Step 1: 發布一則測試貼文
    print("[1] 建立貼文容器...")
    resp = requests.post(f"{BASE}/me/threads", params={
        "access_token": TOKEN,
        "media_type": "TEXT",
        "text": "[API Demo] Testing threads_content_publish permission. This post will be deleted shortly.",
    })
    print(f"    Status: {resp.status_code}")
    container = resp.json()
    container_id = container.get("id")
    print(f"    Container ID: {container_id}")

    if not container_id:
        print(f"    Error: {container}")
        return

    # Step 2: 發布
    print("\n[2] 發布貼文...")
    resp = requests.post(f"{BASE}/me/threads_publish", params={
        "access_token": TOKEN,
        "creation_id": container_id,
    })
    print(f"    Status: {resp.status_code}")
    published = resp.json()
    post_id = published.get("id")
    print(f"    Published Post ID: {post_id}")

    if not post_id:
        print(f"    Error: {published}")
        return

    # Step 3: 讀取自己貼文的回覆 (threads_manage_replies)
    print("\n[3] 讀取貼文回覆 (threads_manage_replies)...")
    time.sleep(2)  # 等一下讓 API 同步
    resp = requests.get(f"{BASE}/{post_id}/replies", params={
        "access_token": TOKEN,
        "fields": "id,text,username,timestamp",
    })
    print(f"    Status: {resp.status_code}")
    replies = resp.json().get("data", [])
    print(f"    Replies found: {len(replies)}")

    # Step 4: 讀取最近的貼文列表
    print("\n[4] 讀取最近貼文列表...")
    resp = requests.get(f"{BASE}/me/threads", params={
        "access_token": TOKEN,
        "fields": "id,text,timestamp",
        "limit": 3,
    })
    print(f"    Status: {resp.status_code}")
    posts = resp.json().get("data", [])
    for p in posts:
        text_preview = p.get("text", "")[:50].encode("ascii", "replace").decode()
        print(f"    - {p['id']}: {text_preview}...")

    # Step 5: 刪除測試貼文
    print(f"\n[5] 刪除測試貼文 {post_id}...")
    resp = requests.delete(f"{BASE}/{post_id}", params={
        "access_token": TOKEN,
    })
    print(f"    Status: {resp.status_code}")
    print("    Test post deleted.")

    print("\n=== Demo 完成 ===")


if __name__ == "__main__":
    main()
