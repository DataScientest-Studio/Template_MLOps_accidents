"""
In-memory auth rate limiting and failed-login lockout.

Per-username rate limits for login and refresh; failed-login tracking and
account lockout. Not shared across replicas; multi-instance would need Redis.
"""

from datetime import datetime, timedelta
from typing import Tuple

from .config import settings

# -----------------------------------------------------------------------------
# Rate limit: fixed-window, key = (identifier, window_id)
# -----------------------------------------------------------------------------

_rate_store: dict[Tuple[str, str], Tuple[int, datetime]] = {}


def _window_id(identifier: str, window_seconds: int) -> str:
    """Fixed window id (start of window as epoch bucket)."""
    # Use a stable bucket so all requests in same window share same key
    # Bucket = (now // window_seconds) * window_seconds
    now = datetime.utcnow()
    bucket_epoch = int(now.timestamp()) // window_seconds * window_seconds
    return f"{identifier}:{bucket_epoch}"


def check_rate_limit(
    identifier: str,
    limit: int,
    window_seconds: int,
    key_prefix: str = "",
) -> bool:
    """
    Return True if under limit (allowed), False if over limit (should 429).
    """
    key = (key_prefix + identifier, _window_id(identifier, window_seconds))
    if key not in _rate_store:
        return True
    count, _ = _rate_store[key]
    return count < limit


def record_rate_limit_request(
    identifier: str,
    window_seconds: int,
    key_prefix: str = "",
) -> None:
    """Increment request count for this identifier in current window."""
    key = (key_prefix + identifier, _window_id(identifier, window_seconds))
    now = datetime.utcnow()
    window_end = now + timedelta(seconds=window_seconds)
    if key not in _rate_store:
        _rate_store[key] = (1, window_end)
    else:
        count, end = _rate_store[key]
        _rate_store[key] = (count + 1, end)
    # Optional: prune old keys (same identifier, old windows) to avoid unbounded growth
    _prune_rate_windows(identifier, key_prefix, window_seconds)


def _prune_rate_windows(identifier: str, key_prefix: str, window_seconds: int) -> None:
    """Remove expired window entries for this identifier."""
    now = datetime.utcnow()
    to_del = [
        k
        for k, (_, end) in _rate_store.items()
        if k[0] == key_prefix + identifier and end < now
    ]
    for k in to_del:
        del _rate_store[k]


# -----------------------------------------------------------------------------
# Lockout: failed login count and locked_until per username
# -----------------------------------------------------------------------------

_lockout_store: dict[str, Tuple[int, datetime | None]] = (
    {}
)  # username -> (failed_count, locked_until)


def check_lockout(username: str) -> Tuple[bool, float | None]:
    """
    Return (is_locked, minutes_remaining).
    If not locked, minutes_remaining is None.
    """
    if username not in _lockout_store:
        return False, None
    failed_count, locked_until = _lockout_store[username]
    if locked_until is None:
        return False, None
    now = datetime.utcnow()
    if now >= locked_until:
        # Lock expired; clear so next failed attempt starts fresh
        _lockout_store[username] = (0, None)
        return False, None
    delta = locked_until - now
    minutes = max(0.0, delta.total_seconds() / 60.0)
    return True, round(minutes, 1)


def record_failed_login(username: str) -> None:
    """Increment failed count; set locked_until when max attempts reached."""
    now = datetime.utcnow()
    lockout_minutes = settings.LOGIN_LOCKOUT_MINUTES
    max_attempts = settings.MAX_FAILED_LOGIN_ATTEMPTS

    if username not in _lockout_store:
        _lockout_store[username] = (1, None)

    failed_count, locked_until = _lockout_store[username]
    if locked_until is not None and now >= locked_until:
        # Previous lock expired; reset
        failed_count = 0
        locked_until = None

    failed_count += 1
    if failed_count >= max_attempts:
        locked_until = now + timedelta(minutes=lockout_minutes)
    _lockout_store[username] = (failed_count, locked_until)


def clear_failed_logins(username: str) -> None:
    """Clear failed count and lock for username (on successful login)."""
    if username in _lockout_store:
        _lockout_store[username] = (0, None)
