"""CLI 輸出格式化（JSON / 人讀）。"""

import json
import sys
from typing import Any, NoReturn


def emit(data: Any, *, json_mode: bool = False, message: str | None = None) -> None:
    """印出資料；JSON 模式印合法 JSON，否則人讀。"""
    if json_mode:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    if message:
        print(message)
    if isinstance(data, dict):
        for k, v in data.items():
            print(f"  {k}: {v}")
    elif isinstance(data, list):
        for item in data:
            print(f"  - {item}")
    else:
        print(data)


def error(message: str, *, exit_code: int = 1) -> NoReturn:
    """印 error 到 stderr 並 exit（raises SystemExit）。

    Callers 不需要加 return — 此函式一定 exit。
    """
    print(f"[ERROR] {message}", file=sys.stderr)
    sys.exit(exit_code)


def warn(message: str) -> None:
    """印 warning 到 stderr（不 exit）。"""
    print(f"[WARN] {message}", file=sys.stderr)
