"""Delete 備份邏輯——把刪除前的貼文內容寫到 .deleted_posts/。

Spec Section 3：
- 檔名 `{post_id}_{YYYYMMDD-HHMMSS}.json`
- Metadata: captured_at（ISO 時間戳）、captured_before_delete: true
- 若備份失敗則**不執行 DELETE**（handler 職責）
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class BackupError(Exception):
    """備份失敗——含原始 exception 的訊息。"""


def save_delete_backup(
    *,
    post_id: str,
    post_data: dict[str, Any],
    backup_dir: Path,
) -> Path:
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    filename = f"{post_id}_{timestamp}.json"

    envelope = {
        "captured_at": now.isoformat(),
        "captured_before_delete": True,
        "post": post_data,
    }

    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise BackupError(f"Cannot create backup directory {backup_dir}: {e}") from e

    target = backup_dir / filename
    try:
        target.write_text(
            json.dumps(envelope, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as e:
        raise BackupError(f"Cannot write backup file {target}: {e}") from e

    return target
