"""CLI 層單元測試。"""

import subprocess
import sys
from unittest.mock import patch

import pytest


def test_threads_cli_version():
    """threads --version 應印出版本號。"""
    result = subprocess.run(
        [sys.executable, "-m", "threads_pipeline.threads_cli.cli", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "0.1.0" in result.stdout


def test_threads_cli_help():
    """threads --help 應印使用說明且 exit 0。"""
    result = subprocess.run(
        [sys.executable, "-m", "threads_pipeline.threads_cli.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "posts" in result.stdout or "post" in result.stdout
