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


def emit_envelope_json(
    data: Any,
    *,
    warnings: list[dict[str, str]] | None = None,
    next_cursor: str | None = None,
) -> None:
    """印 JSON envelope 到 stdout。

    Schema（spec Section 3）：
        {"ok": true, "data": ...}
        + 可選 "warnings": [{"code": ..., "message": ...}, ...]
        + 可選 "next_cursor": "..."
    """
    envelope: dict[str, Any] = {"ok": True, "data": data}
    if warnings:
        envelope["warnings"] = warnings
    if next_cursor:
        envelope["next_cursor"] = next_cursor
    print(json.dumps(envelope, ensure_ascii=False, indent=2))


def emit_error_json(code: str, message: str) -> None:
    """印失敗 envelope 到 stdout（不 exit；供 error_with_code 使用）。"""
    envelope = {"ok": False, "error": {"code": code, "message": message}}
    print(json.dumps(envelope, ensure_ascii=False))


def error_with_code(
    code: str,
    message: str,
    *,
    json_mode: bool = False,
    exit_code: int = 1,
) -> NoReturn:
    """統一錯誤輸出：JSON mode 加 envelope、人類 mode 只 stderr [ERROR]，最後 exit。

    呼叫者不需要加 return — 此函式一定 exit。
    """
    if json_mode:
        emit_error_json(code, message)
    print(f"[ERROR] {message}", file=sys.stderr)
    sys.exit(exit_code)


def warn_with_code(code: str, message: str) -> dict[str, str]:
    """印 stderr [WARN] + 回傳 envelope warnings 陣列要放的 dict。

    設計理由：warnings 同時要走 stderr（人類看得到）與 JSON envelope
    （Agent 收得到），此 helper 一次處理兩邊。
    """
    print(f"[WARN] {message}", file=sys.stderr)
    return {"code": code, "message": message}
