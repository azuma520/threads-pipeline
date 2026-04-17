"""JSON envelope helpers 的 unit test。"""

import json
import sys

import pytest

from threads_pipeline.threads_cli.output import (
    emit_envelope_json,
    emit_error_json,
    error_with_code,
    warn_with_code,
)


# === emit_envelope_json ===

def test_envelope_json_minimal(capsys):
    """只有 data 的 envelope 應輸出 ok:true + data。"""
    emit_envelope_json({"foo": "bar"})
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed == {"ok": True, "data": {"foo": "bar"}}
    assert captured.err == ""


def test_envelope_json_with_warnings(capsys):
    """有 warnings 應放在 envelope 內。"""
    emit_envelope_json(
        {"x": 1},
        warnings=[{"code": "FOO", "message": "bar"}],
    )
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["warnings"] == [{"code": "FOO", "message": "bar"}]


def test_envelope_json_with_next_cursor(capsys):
    """有 next_cursor 應放在 envelope 內。"""
    emit_envelope_json({"posts": []}, next_cursor="abc123")
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["next_cursor"] == "abc123"


def test_envelope_json_preserves_cjk(capsys):
    """中文字不應被 ASCII-escape。"""
    emit_envelope_json({"text": "測試"})
    captured = capsys.readouterr()
    assert "測試" in captured.out
    assert "\\u" not in captured.out


# === emit_error_json ===

def test_error_json_shape(capsys):
    """error envelope 應 ok:false + error.code + error.message。"""
    emit_error_json("TOKEN_MISSING", "token not set")
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed == {"ok": False, "error": {"code": "TOKEN_MISSING", "message": "token not set"}}


# === error_with_code ===

def test_error_with_code_human_mode(capsys):
    """非 JSON 模式：只 stderr [ERROR]，不印 JSON。"""
    with pytest.raises(SystemExit) as exc_info:
        error_with_code("API_ERROR", "bad stuff", json_mode=False, exit_code=1)
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "[ERROR] bad stuff" in captured.err


def test_error_with_code_json_mode(capsys):
    """JSON 模式：stdout 印 envelope + stderr [ERROR]。"""
    with pytest.raises(SystemExit) as exc_info:
        error_with_code("API_ERROR", "oops", json_mode=True, exit_code=1)
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed == {"ok": False, "error": {"code": "API_ERROR", "message": "oops"}}
    assert "[ERROR] oops" in captured.err


def test_error_with_code_exit_code_2(capsys):
    """exit_code 參數應傳到 SystemExit.code。"""
    with pytest.raises(SystemExit) as exc_info:
        error_with_code("INVALID_ARGS", "bad flag", json_mode=False, exit_code=2)
    assert exc_info.value.code == 2


# === warn_with_code ===

def test_warn_with_code_prints_stderr_and_returns_dict(capsys):
    """warn_with_code 應印 stderr [WARN] + 回傳 dict。"""
    result = warn_with_code("LIMIT_CLAMPED", "limit clamped to 100")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "[WARN] limit clamped to 100" in captured.err
    assert result == {"code": "LIMIT_CLAMPED", "message": "limit clamped to 100"}
