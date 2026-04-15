"""Threads API 發文邏輯層 — publish / reply / chain。

對應 Threads API 兩階段流程：
- Step 1: POST /me/threads （建立 container）
- Step 2: POST /me/threads_publish （publish container）

Reply 跟 publish 共用流程，差別在 Step 1 多一個 reply_to_id 參數。
"""

import os
from typing import Optional

import requests

THREADS_API_BASE = "https://graph.threads.net/v1.0"


class PublishError(Exception):
    """發文失敗的 exception。"""
    pass


def _post(url: str, params: dict, timeout: int = 30) -> dict:
    """POST 並回傳 JSON，失敗 raise PublishError 帶原始錯誤。"""
    try:
        resp = requests.post(url, params=params, timeout=timeout)
    except requests.exceptions.RequestException as e:
        raise PublishError(f"Network error: {e}") from e

    try:
        body = resp.json()
    except ValueError:
        body = {"raw": resp.text}

    if resp.status_code != 200:
        # 防禦性：body["error"] 可能不是 dict（API 有時回 string / null）
        err = body.get("error")
        if isinstance(err, dict):
            err_msg = err.get("message", "Unknown error")
        elif err:
            err_msg = str(err)
        else:
            err_msg = "Unknown error"
        raise PublishError(f"API {resp.status_code}: {err_msg}")
    return body


def publish_text(
    text: str,
    *,
    token: Optional[str] = None,
    reply_to_id: Optional[str] = None,
) -> str:
    """發一則純文字貼文（或回覆），回傳 post_id。

    Args:
        text: 貼文文字內容
        token: Threads access token；None 時從 THREADS_ACCESS_TOKEN 讀
        reply_to_id: 若提供，發為回覆（reply to 該 post_id）

    Returns:
        發出的 post_id

    Raises:
        PublishError: 任一 step 失敗 / token 缺失
    """
    token = token or os.environ.get("THREADS_ACCESS_TOKEN", "")
    if not token:
        raise PublishError("THREADS_ACCESS_TOKEN not set")

    # Step 1: 建立 container
    step1_params = {
        "access_token": token,
        "media_type": "TEXT",
        "text": text,
    }
    if reply_to_id:
        step1_params["reply_to_id"] = reply_to_id

    step1 = _post(f"{THREADS_API_BASE}/me/threads", step1_params)
    container_id = step1.get("id")
    if not container_id:
        raise PublishError(f"Step 1 returned no container ID: {step1}")

    # Step 2: publish
    step2_params = {
        "access_token": token,
        "creation_id": container_id,
    }
    try:
        step2 = _post(f"{THREADS_API_BASE}/me/threads_publish", step2_params)
    except PublishError as e:
        raise PublishError(
            f"Step 2 failed (orphan container_id={container_id}): {e}"
        ) from e

    post_id = step2.get("id")
    if not post_id:
        raise PublishError(f"Step 2 returned no post ID (container_id={container_id}): {step2}")
    return post_id


def reply_to(
    parent_post_id: str,
    text: str,
    *,
    token: Optional[str] = None,
) -> str:
    """回覆既有貼文，回傳回覆的 post_id。

    Args:
        parent_post_id: 要回覆的目標 post ID
        text: 回覆文字內容
        token: Threads access token；None 時從環境讀

    Returns:
        回覆貼文的 post_id

    Raises:
        PublishError: parent_post_id 為空或 API 失敗
    """
    if not parent_post_id:
        raise PublishError("reply_to requires non-empty post_id")
    return publish_text(text, token=token, reply_to_id=parent_post_id)
