"""profile_discovery endpoint 可用性探針。

目的：在送審前實測 `/{username}` 與 `/{username}/threads` 在 Standard Access
下的行為，決定後續 CLI / 腳本 / 影片怎麼寫。

結果解讀：
- /me 失敗 → token 掛了，其他測試無意義
- self（owner）路徑成功但 other 路徑 lock → Advanced 才解鎖跨帳號，要走 Plan B
- 全成功 → 本輪 live demo 可走 @other_username
- other 路徑也 lock（類似 mentions 500 nonexisting field）→ 要走 Architecture-Demo
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests

# ─── 載入 .env（照 api_explorer.py 現有 pattern） ──────────────────────────
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "")
BASE = "https://graph.threads.net/v1.0"

OWNER = "azuma01130626"        # 本 app owner 帳號
OTHER = "lin__photograph"      # demo 腳本設定的他人帳號目標

if not TOKEN:
    print("[FATAL] 找不到 THREADS_ACCESS_TOKEN（.env 未設或為空）")
    sys.exit(1)


def probe(label: str, url: str, params: dict) -> dict:
    """單一請求。只印非機密 params，回傳精簡結果 dict。"""
    display_params = {k: v for k, v in params.items() if k != "access_token"}
    print(f"\n── {label} ──")
    print(f"  URL:    {url}")
    print(f"  params: {display_params}")

    call_params = {**params, "access_token": TOKEN}
    try:
        resp = requests.get(url, params=call_params, timeout=30)
        status = resp.status_code
        try:
            body = resp.json()
        except Exception:
            body = {"_raw": resp.text[:300]}
    except Exception as exc:
        print(f"  [ERROR] network: {exc}")
        return {"label": label, "ok": False, "status": None, "err": str(exc)}

    # 成功
    if status == 200 and "error" not in body:
        items = body.get("data")
        if isinstance(items, list):
            summary = f"ok — data[{len(items)}]"
            if items:
                sample = items[0]
                keys = ", ".join(list(sample.keys())[:6])
                summary += f"; sample keys: {keys}"
        else:
            keys = ", ".join(list(body.keys())[:8])
            summary = f"ok — top-level keys: {keys}"
        print(f"  [PASS]  status={status} — {summary}")
        return {"label": label, "ok": True, "status": status, "summary": summary}

    # API error
    err = body.get("error") if isinstance(body, dict) else None
    if not isinstance(err, dict):
        err = {}
    msg = err.get("message", "(no message)")
    etype = err.get("type", "-")
    code = err.get("code", "-")
    print(f"  [FAIL]  status={status} code={code} type={etype}")
    print(f"          message: {msg}")
    return {
        "label": label,
        "ok": False,
        "status": status,
        "code": code,
        "type": etype,
        "message": msg,
    }


def main() -> int:
    print("=" * 70)
    print("profile_discovery endpoint 可用性探針")
    print(f"OWNER={OWNER}   OTHER={OTHER}")
    print("=" * 70)

    results = []

    # 1. Token 活性
    results.append(probe(
        "1. Token alive — /me",
        f"{BASE}/me",
        {"fields": "id,username"},
    ))

    # 2. Baseline：自己貼文列（Standard Access 應該可以）
    results.append(probe(
        "2. Baseline — /me/threads",
        f"{BASE}/me/threads",
        {"fields": "id,permalink", "limit": 2},
    ))

    # 3. By-username 路徑：查自己 profile（這條路徑是否通？）
    results.append(probe(
        "3. Self by username — /{owner}",
        f"{BASE}/{OWNER}",
        {"fields": "id,username,threads_biography"},
    ))

    # 4. By-username 列貼文：查自己（Advanced 解鎖對外查，此處驗 self 能不能走這條 URL）
    results.append(probe(
        "4. Self by username — /{owner}/threads",
        f"{BASE}/{OWNER}/threads",
        {"fields": "id,permalink", "limit": 2},
    ))

    # 5. 跨帳號 profile：profile_discovery 的核心 — 查他人 profile
    results.append(probe(
        "5. Other profile — /{other}",
        f"{BASE}/{OTHER}",
        {"fields": "id,username,threads_biography"},
    ))

    # 6. 跨帳號列貼文：profile_discovery 的旗艦 — 列他人公開貼文
    results.append(probe(
        "6. Other posts — /{other}/threads",
        f"{BASE}/{OTHER}/threads",
        {"fields": "id,permalink,text", "limit": 2},
    ))

    # ─── 結論 ────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("結論")
    print("=" * 70)
    for r in results:
        mark = "✅" if r["ok"] else "❌"
        extra = r.get("summary") if r["ok"] else f"({r.get('code')}/{r.get('type')})"
        print(f"  {mark} {r['label']:50s} {extra}")

    token_ok = results[0]["ok"]
    self_me_threads = results[1]["ok"]
    self_by_user_profile = results[2]["ok"]
    self_by_user_threads = results[3]["ok"]
    other_profile = results[4]["ok"]
    other_threads = results[5]["ok"]

    print("\n判讀：")
    if not token_ok:
        print("  ⚠️  TOKEN 失效，其他結果無意義。先 refresh token 再重跑。")
        verdict = "TOKEN_DEAD"
    elif other_threads and other_profile:
        print("  🎯 profile_discovery endpoint **全可用**（跨帳號已通）")
        print("      → demo 腳本可照計畫用 @other 的 URL 錄 live demo")
        print("      → 這很異常——理論上要 Advanced 才解鎖，請實機再驗一次")
        verdict = "FULL_OPEN"
    elif self_by_user_threads and self_by_user_profile and not other_threads:
        print("  🔒 profile_discovery **self-only**（自己 username 可，他人鎖）")
        print("      → 這是 Standard Access 預期行為；demo 用 self URL 示範 flow 即可")
        print("      → Notes 寫明：核准後擴及任意 username")
        verdict = "SELF_ONLY"
    elif not self_by_user_threads and self_me_threads:
        print("  🧊 by-username 路徑**完全鎖**（連自己 username 都不通）")
        print("      → 類似 /me/threads_mentions 的 endpoint-lock 情境")
        print("      → 必須走 Architecture-Demo（CLI 原始碼 + Meta docs + Threads UI）")
        verdict = "ENDPOINT_LOCKED"
    else:
        print("  ⚠️  不在預期的三種狀態，請人工看逐項 [FAIL] 原因")
        verdict = "UNEXPECTED"

    print(f"\nverdict = {verdict}")
    print("=" * 70)

    # 輸出 JSON summary 方便未來 scripts 管道化使用
    summary = {"verdict": verdict, "results": results}
    print("\nJSON summary:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    return 0 if token_ok else 1


if __name__ == "__main__":
    sys.exit(main())
