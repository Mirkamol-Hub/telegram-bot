"""
Auth service — validates Telegram Mini App initData
and resolves user role.
"""

import os
import hmac
import hashlib
import json
from urllib.parse import unquote, parse_qs
from fastapi import HTTPException, Header
from services.sheets import SheetsService

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


def _validate_telegram_init_data(init_data: str) -> dict:
    """
    Validates Telegram WebApp initData per official spec.
    Returns parsed user dict or raises HTTPException.
    """
    if not BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Bot token not configured.")

    parsed = parse_qs(init_data)
    hash_value = parsed.pop("hash", [None])[0]
    if not hash_value:
        raise HTTPException(status_code=401, detail="Missing hash in initData.")

    # Build check string
    data_check_arr = sorted(
        [f"{k}={v[0]}" for k, v in parsed.items()]
    )
    data_check_string = "\n".join(data_check_arr)

    # Compute secret key
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_hash, hash_value):
        raise HTTPException(status_code=401, detail="Invalid Telegram initData signature.")

    user_str = parsed.get("user", [None])[0]
    if not user_str:
        raise HTTPException(status_code=401, detail="No user in initData.")
    return json.loads(unquote(user_str))


def get_current_user(
    x_init_data: str = Header(None, alias="X-Telegram-Init-Data"),
    x_telegram_id: str = Header(None, alias="X-Telegram-ID"),  # dev bypass
) -> dict:
    """
    FastAPI dependency — resolves current user from Telegram headers.
    In development, pass X-Telegram-ID header to bypass signature check.
    """
    sheets = SheetsService()

    # Development bypass
    dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
    if dev_mode and x_telegram_id:
        role = sheets.get_user_role(x_telegram_id)
        return {"id": int(x_telegram_id), "role": role}

    if not x_init_data:
        raise HTTPException(status_code=401, detail="Missing X-Telegram-Init-Data header.")

    user_data = _validate_telegram_init_data(x_init_data)
    telegram_id = str(user_data.get("id", ""))
    role = sheets.get_user_role(telegram_id)
    return {**user_data, "role": role}


def require_role(*roles: str):
    """Role guard — returns FastAPI dependency."""
    def dependency(current_user: dict = None):
        # Used inline, not as FastAPI Depends directly
        if current_user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions.")
        return current_user
    return dependency
