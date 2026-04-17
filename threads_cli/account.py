"""threads account 子命令群——info / insights。"""

import requests
import typer

from threads_pipeline.threads_client import (
    fetch_account_info,
    fetch_account_insights_cli,
)
from threads_pipeline.threads_cli.output import (
    emit_envelope_json,
    error_with_code,
)
from threads_pipeline.threads_cli.safety import require_token

account_app = typer.Typer(help="Account operations", no_args_is_help=True)


@account_app.command("info")
def info_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON envelope"),
):
    """Fetch account basic info (/me)."""
    token = require_token()
    try:
        data = fetch_account_info(token)
    except requests.exceptions.RequestException as e:
        error_with_code("API_ERROR", f"Threads API error: {e}", json_mode=json_mode, exit_code=1)

    if json_mode:
        emit_envelope_json(data)
        return

    # 人類模式
    print("[OK] Account info:")
    print(f"  id:          {data.get('id', '(missing)')}")
    print(f"  username:    {data.get('username', '(missing)')}")
    if bio := data.get("threads_biography"):
        print(f"  biography:   {bio}")
    if pic := data.get("threads_profile_picture_url"):
        print(f"  profile_pic: {pic}")


@account_app.command("insights")
def insights_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON envelope"),
):
    """Fetch account-level insights (views / followers 等)."""
    token = require_token()
    try:
        data = fetch_account_insights_cli(token)
    except requests.exceptions.RequestException as e:
        error_with_code("API_ERROR", f"Threads API error: {e}", json_mode=json_mode, exit_code=1)

    if json_mode:
        emit_envelope_json(data)
        return

    print("[OK] Account insights:")
    for metric in data.get("data", []):
        name = metric.get("name", "?")
        values = metric.get("values", [])
        if values:
            val = values[0].get("value")
            print(f"  {name:30s} {val}")
