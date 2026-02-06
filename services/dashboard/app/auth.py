"""
Authentication and RBAC for Streamlit dashboard.
Uses existing Auth API (JWT). Custom logic for API-backed auth.
"""

from __future__ import annotations

import os
import time
from typing import Any, Optional

import httpx

from .config import API_BASE_URL

# Session state keys
TOKEN_KEY = "access_token"
REFRESH_KEY = "refresh_token"
EXPIRES_AT_KEY = "token_expires_at"
USER_KEY = "user"


def get_api_base() -> str:
    return os.environ.get("API_BASE_URL", API_BASE_URL).rstrip("/")


def login(username: str, password: str) -> tuple[bool, Any]:
    """
    POST /api/v1/auth/login.
    Returns (True, data_dict) on success, (False, error_message) on failure.
    """
    try:
        with httpx.Client(base_url=get_api_base(), timeout=15.0) as client:
            r = client.post(
                "/api/v1/auth/login",
                json={"username": username, "password": password},
            )
            if r.status_code != 200:
                detail = "Login failed"
                try:
                    detail = r.json().get("detail", detail)
                except Exception:
                    pass
                return False, detail
            return True, r.json()
    except Exception as e:
        return False, str(e)


def fetch_me(access_token: str) -> Optional[dict]:
    """GET /api/v1/auth/me. Returns user dict or None."""
    try:
        with httpx.Client(base_url=get_api_base(), timeout=10.0) as client:
            r = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if r.status_code != 200:
                return None
            return r.json()
    except Exception:
        return None


def is_admin(role: str) -> bool:
    return (role or "").lower() == "admin"


def session_expired(expires_at: float) -> bool:
    return time.time() >= expires_at


def forgot_password(username: str) -> tuple[bool, Any]:
    """
    POST /api/v1/auth/forgot-password.
    Returns (True, data_dict with optional reset_token) on success, (False, error_message) on failure.
    """
    try:
        with httpx.Client(base_url=get_api_base(), timeout=15.0) as client:
            r = client.post(
                "/api/v1/auth/forgot-password",
                json={"username": username},
            )
            if r.status_code != 200:
                detail = "Request failed"
                try:
                    detail = r.json().get("detail", detail)
                except Exception:
                    pass
                return False, detail
            return True, r.json()
    except Exception as e:
        return False, str(e)


def reset_password(token: str, new_password: str) -> tuple[bool, Any]:
    """
    POST /api/v1/auth/reset-password.
    Returns (True, None) on success, (False, error_message) on failure.
    """
    try:
        with httpx.Client(base_url=get_api_base(), timeout=15.0) as client:
            r = client.post(
                "/api/v1/auth/reset-password",
                json={"token": token, "new_password": new_password},
            )
            if r.status_code == 204:
                return True, None
            detail = "Reset failed"
            try:
                detail = r.json().get("detail", detail)
            except Exception:
                pass
            return False, detail
    except Exception as e:
        return False, str(e)
